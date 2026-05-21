import json
import os
import sys
from datetime import datetime, timezone
from functools import partial

from opensearchpy import TransportError
from opensearchpy.helpers import bulk

from common.log import setup_logging

BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10000))
SETTINGS_FILE = "complaints/settings.json"
MAPPING_FILE = "complaints/ccdb/ccdb_mapping.json"

DATE_INDEXED = os.getenv("DATE_INDEXED", datetime.now(timezone.utc).isoformat())

logger = setup_logging("index_ccdb")

# -----------------------------------------------------------------------------
# Enhancing Functions
# -----------------------------------------------------------------------------


def enhance_complaint(complaint):
    if "complaint_id" not in complaint:
        complaint["complaint_id"] = complaint["public_id"]

    s = complaint.get("complaint_what_happened")

    # Add this field
    complaint["has_narrative"] = s != "" and s is not None
    complaint["date_indexed"] = DATE_INDEXED

    # Set all values with empty strings to None to comply with V1
    # logic
    normalized_complaint = {k: v if v != "" else None for k, v in complaint.items()}
    # Restore complaint_what_happened to prevent ES queries from breaking
    normalized_complaint["complaint_what_happened"] = s
    return normalized_complaint


# -----------------------------------------------------------------------------
# Original Functions
# -----------------------------------------------------------------------------


def update_indexes_in_alias(es, alias, backup_index_name, index_name):
    """cycle alias from backup if it exists, or add index,
    or add index and alias"""
    if es.indices.exists_alias(name=alias):
        if es.indices.exists_alias(name=alias, index=backup_index_name):
            logger.info(
                "Removing from alias %s index %s and adding %s"
                % (alias, backup_index_name, index_name)
            )
            es.indices.update_aliases(
                body={
                    "actions": [
                        {"remove": {"index": backup_index_name, "alias": alias}},
                        {"add": {"index": index_name, "alias": alias}},
                    ]
                }
            )
        else:
            logger.info(
                "Alias %s exists so just add index %s to it" % (alias, index_name)
            )
            es.indices.update_aliases(
                body={"actions": [{"add": {"index": index_name, "alias": alias}}]}
            )
    else:
        logger.info("Adding alias %s for index %s" % (alias, index_name))
        es.indices.put_alias(name=alias, index=index_name)


def swap_backup_index(es, alias, index_name, backup_index_name):
    if es.indices.exists_alias(name=alias):
        if es.indices.exists_alias(name=alias, index=index_name):
            logger.info(
                f"Alias points to index {index_name}.\nSwitching index variables."
            )
            backup_index_name, index_name = index_name, backup_index_name
        else:
            logger.info(
                "Alias exists but doesn't point to {index_name}.\nKeeping index variables."
            )
    return index_name, backup_index_name


def load_json(file):
    with open(file) as settings_file:
        try:
            jo = json.load(settings_file)
        except Exception:
            logger.error("Warning: file %s is in invalid json format.", file)
            sys.exit(-1)
    return jo


def data_load_strategy_complaint(data, transform_fn):
    with open(data) as f:
        for line in f:
            doc = transform_fn(json.loads(line))
            yield {"_op_type": "index", "_id": doc["complaint_id"], "_source": doc}


def yield_chunked_docs(get_data_function, data, chunk_size):
    count = 0
    doc_ary = []
    for doc in get_data_function(data):
        doc_ary.append(doc)
        count += 1
        if count == chunk_size:
            yield doc_ary
            doc_ary = []
            count = 0
    yield doc_ary


def update_index_with_data(es, data, index_name, chunk_size=BATCH_SIZE):
    logger.info(f"Loading data into {index_name}")

    get_data_fn = partial(data_load_strategy_complaint, transform_fn=enhance_complaint)
    total_rows_of_data = 0

    for doc_ary in yield_chunked_docs(get_data_fn, data, chunk_size):
        logger.info("chunk retrieved, now bulk load")
        success, _ = bulk(
            es, actions=doc_ary, index=index_name, chunk_size=chunk_size, refresh=False
        )
        total_rows_of_data += success
        logger.info(
            "{:,d} records indexed, total = {:,d}".format(success, total_rows_of_data)
        )

    logger.info(f"Refreshing index {index_name}")
    es.indices.refresh(index=index_name)


def reindex_json_data(es, data, alias):
    settings = load_json(SETTINGS_FILE)
    mapping = load_json(MAPPING_FILE)

    index_name = f"{alias}-v1"
    backup_index_name = f"{alias}-v2"

    es.indices.create(index=index_name, ignore=400)
    es.indices.create(index=backup_index_name, ignore=400)

    index_name, backup_index_name = swap_backup_index(
        es, alias, index_name, backup_index_name
    )
    logger.info(f"Deleting and recreating {index_name}")
    es.indices.delete(index=index_name)
    logger.debug("Creating %s with mappings and settings" % index_name)
    es.indices.create(
        index=index_name, body={"settings": settings, "mappings": mapping}
    )

    try:
        update_index_with_data(es, data, index_name)
        update_indexes_in_alias(es, alias, backup_index_name, index_name)
    except TransportError as e:
        logger.error(
            "Error while loading data. Reverting alias to original state after: %s" % e
        )
        es.indices.put_alias(name=alias, index=backup_index_name)
        sys.exit(e.error)

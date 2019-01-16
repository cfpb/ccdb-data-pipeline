import os
import sys
import json
from elasticsearch import TransportError
from elasticsearch.helpers import bulk


def update_indexes_in_alias(es, logger, alias, backup_index_name, index_name):
    ''' cycle alias from backup if it exists, or add index,
        or add index and alias'''
    if es.indices.exists_alias(name=alias):
        if es.indices.exists_alias(name=alias, index=backup_index_name):
            logger.info("Removing from alias %s index %s and adding %s" %
                        (alias, backup_index_name, index_name))
            es.indices.update_aliases(body={
                "actions": [
                    {"remove": {"index": backup_index_name, "alias": alias}},
                    {"add": {"index": index_name, "alias": alias}}
                ]
            })
        else:
            logger.info("Alias %s exists so just add index %s to it" %
                        (alias, index_name))
            es.indices.update_aliases(body={
                "actions": [
                    {"add": {"index": index_name, "alias": alias}}
                ]
            })
    else:
        logger.info("Adding alias %s for index %s" % (alias, index_name))
        es.indices.put_alias(name=alias, index=index_name)


def swap_backup_index(es, logger, alias, index_name, backup_index_name):
    if es.indices.exists_alias(name=alias):
        if es.indices.exists_alias(name=alias, index=index_name):
            logger.info(
                "Alias Exists for index %s.\nSwitiching to backup index %s."
                % (index_name, backup_index_name)
            )
            backup_index_name, index_name = index_name, backup_index_name
        else:
            logger.info(
                "Alias Exists for index %s.\nSwitiching to backup index %s."
                % (backup_index_name, index_name)
            )
    return index_name, backup_index_name


def load_json(logger, file):
    with open(file) as settings_file:
        try:
            jo = json.load(settings_file)
        except Exception:
            logger.error("Warning: file %s is in invalid json format.", file)
            sys.exit(-1)
    return jo


def data_load_strategy_complaint(data):
    with open(data) as f:
        for line in f.readlines():
            doc = json.loads(line)
            yield {'_op_type': 'create',
                   '_id': doc['complaint_id'],
                   '_source': doc}


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


def index_json_data(
    es, logger, doc_type_name, settings_json, mapping_json, data, index_name,
    backup_index_name, alias, chunk_size=20000
):
    settings = load_json(logger, settings_json)
    mapping = load_json(logger, mapping_json)

    es.indices.create(index=index_name, ignore=400)
    es.indices.create(index=backup_index_name, ignore=400)
    index_name, backup_index_name = swap_backup_index(
        es, logger, alias, index_name, backup_index_name
    )
    logger.info("Deleting and recreating %s" % index_name)
    es.indices.delete(index=index_name)
    logger.debug("Creating %s with mappings and settings" % index_name)
    es.indices.create(
        index=index_name,
        body={
            "settings": settings,
            "mappings": {doc_type_name: mapping}
        }
    )
    logger.info(
        "Loading data into %s with doc_type %s"
        % (index_name, doc_type_name)
    )
    try:
        total_rows_of_data = 0
        for doc_ary in yield_chunked_docs(
            data_load_strategy_complaint, data, chunk_size
        ):
            logger.info("chunk retrieved, now bulk load")
            success, _ = bulk(
                es, actions=doc_ary, index=index_name,
                doc_type=doc_type_name, chunk_size=chunk_size, refresh=True
            )
            total_rows_of_data += success
            logger.info(
                "%d records indexed, total = %d"
                % (success, total_rows_of_data)
            )
        update_indexes_in_alias(
            es, logger, alias, backup_index_name, index_name
        )
    except TransportError as e:
        logger.error(
            "Error while loading data. Reverting alias to original "
            "state after: %s" % e
        )
        es.indices.put_alias(name=alias, index=backup_index_name)
        sys.exit(e.error)


if __name__ == '__main__':
    index_json_data()

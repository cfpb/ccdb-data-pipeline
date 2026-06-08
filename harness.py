import argparse
import os
import subprocess

from common.es_proxy import get_es_connection, get_last_indexed
from common.log import setup_logging
from common.s3_utils import create_zipped_archives, update_zipped_archives
from complaints.ccdb.index_ccdb import reindex_json_data, update_index_with_data
from salesforce.connection import session_id
from salesforce.query import full_query, get_time_slice

logger = setup_logging("harness")


def build_arg_parser():
    p = argparse.ArgumentParser(
        prog="harness",
        description="Collect data from Salesforce and index it into Opensearch",
    )

    p.add_argument(
        "--alias",
        default="complaint-public",
        help="Opensearch alias name",
    )

    p.add_argument(
        "--reindex",
        action="store_true",
        help="Whether to add to or replace an index",
    )

    return p


def main():
    p = build_arg_parser()
    args = p.parse_args()

    logger.info("Running indexing harness")
    logger.info("Creating Opensearch Connection")

    es = get_es_connection()
    query = ""

    if args.reindex:
        query = full_query
        logger.info("Getting all data")
    else:
        timestamp = get_last_indexed(es, args.alias)
        query = get_time_slice(timestamp)
        logger.info(f"Getting data since: {timestamp}")

    org = os.getenv("SALESFORCE_DOMAIN")

    subprocess.run(
        [
            "sf",
            "config",
            "set",
            f"org-instance-url=https://{org}.salesforce.com",
            "--global",
        ],
        check=True,
    )

    subprocess.run(
        [
            "sf",
            "data",
            "export",
            "bulk",
            "--query",
            query,
            "--output-file",
            "salesforce_data.csv",
            "--wait",
            "120",
            "--target-org",
            session_id,
        ],
        check=True,
    )

    logger.info("Converting salesforce data to indexable ndjson")

    subprocess.run(
        [
            "python",
            "common/csv2json.py",
            "--fields",
            "complaints/ccdb/fields-s3/v1-json.txt",
            "salesforce_data.csv",
            "to_index.json",
        ],
        check=True,
    )

    bucket = os.getenv("S3_BUCKET")
    prefix = "ccdb/"
    basename = "complaints"

    if args.reindex:
        logger.info("Reindexing data in Opensearch")
        reindex_json_data(es, "to_index.json", args.alias)
        create_zipped_archives(bucket, prefix, basename, "salesforce_data.csv")
    else:
        logger.info("Adding data to existing Opensearch index")
        update_index_with_data(es, "to_index.json", args.alias)
        update_zipped_archives(bucket, prefix, basename, "salesforce_data.csv")


if __name__ == "__main__":
    main()

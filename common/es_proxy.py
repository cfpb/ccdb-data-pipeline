import os
from urllib.parse import quote

from opensearchpy import OpenSearch


def get_es_connection():
    host = os.getenv("ES_HOST")
    uname = os.getenv("ES_USERNAME")
    pw = os.getenv("ES_PASSWORD")
    port = os.getenv("ES_PORT")

    if uname and pw:
        encoded_username = quote(uname)
        encoded_password = quote(pw)
        host = f'{encoded_username}:{encoded_password}@{host}'

    es = OpenSearch(
        f'http://{host}:{port}',
        use_ssl=(str(port) == '443'),
        timeout=2000
    )
    return es


def get_last_indexed(es, index):
    body = {
        "size": 0,
        "aggs": {
            "max_indexed_date": {
                "max": {
                    "field": "date_indexed"
                }
            }
        }
    }
    res = es.search(index=index, body=body)
    return res["aggregations"]["max_indexed_date"]["value_as_string"]

import sys
import os


def alias_to_index_name(es, logger, alias, suffix=''):
    ''' figure out the correct index name -- should be alias-v1 or alias-v2 by convention '''
    index_name = alias + suffix + '-v1'
    if not es.indices.exists_alias(name=alias, index=index_name):
        index_name = alias + suffix + '-v2'
    if not es.indices.exists_alias(name=alias, index=index_name):
        logger.info("index %s-v1/-v2 does not exists" % alias + suffix)
        sys.exit()
    return index_name


def index_taxonomy(es, logger, taxonomy_text, alias):
    mapping = {'_all': {'type': 'string'},
               'properties': {
                    'suggest': {'type': 'completion',
                                'analyzer': 'standard',
                                'search_analyzer': 'standard',
                                'payloads': False,
                                },
                    'text': {'type': 'string'}
                    }
                }

    with open(taxonomy_text) as f:
        words = f.read().split('\n')

    doc = {"suggest": words}

    index_name = alias_to_index_name(es, logger, alias)

    logger.info("Begin updating taxonomy for %s" % index_name)
    es.indices.put_mapping(
        index=index_name,
        doc_type='taxonomy',
        body={'taxonomy': mapping}
    )

    logger.info("Indexing taxonomy...")
    es.index(body=doc, index=index_name, doc_type='taxonomy', id=1, refresh=True)
    logger.info("Completed indexing taxonomy")
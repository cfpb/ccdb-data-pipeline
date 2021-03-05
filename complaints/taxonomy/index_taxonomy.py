import sys

import configargparse

from common.es_proxy import add_basic_es_arguments, get_es_connection
from common.log import setup_logging

# -----------------------------------------------------------------------------
# Original Functions
# -----------------------------------------------------------------------------


def alias_to_index_name(es, logger, alias, suffix=''):
    ''' figure out the correct index name -- should be alias-v1 or alias-v2
        by convention '''
    index_name = alias + suffix + '-v1'
    if not es.indices.exists_alias(name=alias, index=index_name):
        index_name = alias + suffix + '-v2'
    if not es.indices.exists_alias(name=alias, index=index_name):
        logger.info("index %s-v1/-v2 does not exists" % alias + suffix)
        sys.exit()
    return index_name


def index_taxonomy(es, logger, taxonomy_text, alias):
    mapping = {
        '_all': {'type': 'text'},
        'properties': {
            'suggest': {'type': 'completion',
                        'analyzer': 'standard',
                        'search_analyzer': 'standard'
                        },
            'text': {'type': 'text'},
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
    es.index(
        body=doc, index=index_name, doc_type='taxonomy', id=1, refresh=True
    )
    logger.info("Completed indexing taxonomy")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def build_arg_parser():
    p = configargparse.ArgParser(
        prog='index_taxonomy',
        description='fill Elasticsearch with taxonomy data',
        ignore_unknown_config_file_keys=True,
        default_config_files=['./config.ini'],
        args_for_setting_config_path=['-c', '--config'],
        args_for_writing_out_config_file=['--save-config']
    )
    p.add('--dump-config', action='store_true', dest='dump_config',
          help='dump config vars and their source')
    group = add_basic_es_arguments(p)
    group = p.add_argument_group('Files')
    group.add('--taxonomy', dest='taxonomy', required=True,
              help="Taxonomy data")
    return p


def main():
    p = build_arg_parser()
    cfg = p.parse_args()

    logger = setup_logging('taxonomy')

    if cfg.dump_config:
        logger.info('Running index_taxonomy with')
        logger.info(p.format_values())

    es = get_es_connection(cfg)

    logger.info("Begin indexing taxonomy data in Elasticsearch")
    index_taxonomy(es, logger, cfg.taxonomy, cfg.index_name)


if __name__ == '__main__':
    main()

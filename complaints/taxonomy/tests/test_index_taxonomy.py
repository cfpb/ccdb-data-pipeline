import unittest
from unittest.mock import ANY, Mock, patch

import complaints.taxonomy.index_taxonomy as sut
from common.tests import build_argv, captured_output


def toAbsolute(relative):
    import os

    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, relative)

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------


class TestMain(unittest.TestCase):
    def setUp(self):
        self.optional = [
            '--es-host', 'www.example.com',
            '--index-name', 'peach',
            '--taxonomy', toAbsolute('../taxonomy.txt')
        ]

    # --------------------------------------------------------------------------
    # Tests

    @patch('complaints.taxonomy.index_taxonomy.get_es_connection')
    @patch('complaints.taxonomy.index_taxonomy.setup_logging')
    def test_main_happy_path(self, logger_setup, es_conn):
        logger = Mock()
        logger_setup.return_value = logger

        es = Mock()
        es.indices.exists_alias.side_effect = [True, True]
        es_conn.return_value = es

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            sut.main()

        # Not creating indices
        es.indices.create.assert_not_called()

        # Not staging aliases
        es.indices.put_alias.assert_not_called()
        es.indices.delete.assert_not_called()

        # Directly writing the mapping
        es.indices.put_mapping.assert_called_once_with(index='peach-v1',
                                                       doc_type='taxonomy',
                                                       body=ANY)

        # Indexing
        es.index.assert_called_once_with(
            body=ANY, index='peach-v1', doc_type='taxonomy', id=1, refresh=True
        )

        logger.info.assert_any_call('Begin updating taxonomy for peach-v1')
        logger.info.assert_any_call('Indexing taxonomy...')
        logger.info.assert_any_call('Completed indexing taxonomy')

    @patch('complaints.taxonomy.index_taxonomy.get_es_connection')
    @patch('complaints.taxonomy.index_taxonomy.setup_logging')
    def test_main_dump_config(self, logger_setup, es_conn):
        logger = Mock()
        logger_setup.return_value = logger

        es = Mock()
        es.indices.exists_alias.side_effect = [True, True]
        es_conn.return_value = es

        self.optional.insert(0, '--dump-config')

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            sut.main()

        logger.info.assert_any_call('Running index_taxonomy with')

    # -------------------------------------------------------------------------
    # Index taxonomy assumes it is always called after complaint indexing
    # So there is no need to create the alias

    def test_alias_to_index_name_happy_path(self):
        logger = Mock()
        es = Mock()
        es.indices.exists_alias.side_effect = [True, True]
        actual = sut.alias_to_index_name(es, logger, 'peach')
        self.assertEqual('peach-v1', actual)

    def test_alias_to_index_name_no_v1(self):
        logger = Mock()
        es = Mock()
        es.indices.exists_alias.side_effect = [False, True]
        actual = sut.alias_to_index_name(es, logger, 'peach')
        self.assertEqual('peach-v2', actual)

    def test_alias_to_index_name_neither(self):
        logger = Mock()
        es = Mock()
        es.indices.exists_alias.side_effect = [False, False]
        with self.assertRaises(SystemExit):
            sut.alias_to_index_name(es, logger, 'peach')

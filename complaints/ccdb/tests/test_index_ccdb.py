import unittest
from unittest.mock import ANY, Mock, patch

from freezegun import freeze_time

import complaints.ccdb.index_ccdb as sut
from common.tests import build_argv, captured_output


def toAbsolute(relative):
    import os

    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, relative)


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------


class TestIndexCCDB(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()

    def test_update_indexes_in_alias__happy_path(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [True, True]
        expected = {
            'actions': [
                {'remove': {'index': 'baz', 'alias': 'foo'}},
                {'add': {'index': 'bar', 'alias': 'foo'}}
            ]
        }

        sut.update_indexes_in_alias(es, self.logger, 'foo', 'baz', 'bar')
        es.indices.update_aliases.assert_called_once_with(body=expected)

    def test_update_indexes_in_alias__no_aliases(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [False]
        sut.update_indexes_in_alias(es, self.logger, 'foo', 'baz', 'bar')
        es.indices.put_alias.assert_called_once_with(name='foo', index='bar')

    def test_update_indexes_in_alias__no_backup(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [True, False]
        expected = {
            'actions': [
                {'add': {'index': 'bar', 'alias': 'foo'}}
            ]
        }

        sut.update_indexes_in_alias(es, self.logger, 'foo', 'baz', 'bar')
        es.indices.update_aliases.assert_called_once_with(body=expected)

    # -------------------------------------------------------------------------

    def test_swap_backup_index__happy_path(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [True, True]
        a, b = sut.swap_backup_index(es, self.logger, 'foo', 'bar', 'baz')
        self.assertEqual(a, 'baz')
        self.assertEqual(b, 'bar')

    def test_swap_backup_index__no_alias(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [False]
        a, b = sut.swap_backup_index(es, self.logger, 'foo', 'bar', 'baz')
        self.assertEqual(a, 'bar')
        self.assertEqual(b, 'baz')

    def test_swap_backup_index__no_primary(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [True, False]
        a, b = sut.swap_backup_index(es, self.logger, 'foo', 'bar', 'baz')
        self.assertEqual(a, 'bar')
        self.assertEqual(b, 'baz')

    # -------------------------------------------------------------------------

    def test_load_json_happy(self):
        fileName = toAbsolute('../../settings.json')
        actual = sut.load_json(self.logger, fileName)
        self.assertIsNotNone(actual)

    def test_load_json_fail(self):
        fileName = toAbsolute('../../tests/__fixtures__/ccdb.ndjson')
        with self.assertRaises(SystemExit):
            sut.load_json(self.logger, fileName)

    # -------------------------------------------------------------------------

    def test_yield_chunked_docs(self):
        def mock_data_fn(data):
            for x in data:
                yield x

        data = ['foo', 'bar', 'baz', 'qaz', 'quux']
        gen = sut.yield_chunked_docs(mock_data_fn, data, 2)

        actual = next(gen)
        self.assertEqual(actual, ['foo', 'bar'])
        actual = next(gen)
        self.assertEqual(actual, ['baz', 'qaz'])
        rest = [x for x in gen]
        self.assertEqual(rest, [['quux']])


class TestMain(unittest.TestCase):
    def setUp(self):
        self.optional = [
            '--es-host', 'www.example.com',
            '--index-name', 'onion',
            '--settings', toAbsolute('../../settings.json'),
            '--mapping', toAbsolute('../ccdb_mapping.json'),
            '--dataset', toAbsolute('__fixtures__/from_s3.ndjson')
        ]
        self.actual_file = toAbsolute('__fixtures__/actual.json')

    def tearDown(self):
        import os

        try:
            os.remove(self.actual_file)
        except Exception:
            pass

    def capture_actions(self, *args, **kwargs):
        import io
        import json

        with io.open(self.actual_file, mode='w', encoding='utf-8') as f:
            for action in kwargs['actions']:
                f.write(json.dumps(action, ensure_ascii=False))
                f.write('\n')

        return (1001, 99)

    def validate_actions(self, expected_file):
        import io
        import json

        self.maxDiff = None

        with io.open(self.actual_file, 'r', encoding='utf-8') as f:
            actuals = [line for line in f]

        with io.open(expected_file, 'r', encoding='utf-8') as f:
            expecteds = [line for line in f]

        assert len(actuals) == len(expecteds)

        for i, act in enumerate(actuals):
            actual = json.loads(act)
            expected = json.loads(expecteds[i])
            self.assertDictEqual(expected, actual)

    # --------------------------------------------------------------------------
    # Tests

    @patch('complaints.ccdb.index_ccdb.bulk')
    @patch('complaints.ccdb.index_ccdb.get_es_connection')
    @patch('complaints.ccdb.index_ccdb.setup_logging')
    def test_main_happy_path_socrata(self, logger_setup, es_conn, bulk):
        logger = Mock()
        logger_setup.return_value = logger

        es = Mock()
        es.indices.exists_alias.return_value = False
        es_conn.return_value = es

        bulk.side_effect = self.capture_actions

        self.optional.insert(0, '--dump-config')
        self.optional[-1] = toAbsolute('../../tests/__fixtures__/ccdb.ndjson')

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            sut.main()

        # Expected index create calls
        es.indices.create.assert_any_call(index='onion-v1', ignore=400)
        es.indices.create.assert_any_call(index='onion-v2', ignore=400)
        es.indices.create.assert_any_call(index='onion-v1', body=ANY)

        # Expected index put_alias calls
        es.indices.put_alias.assert_called_once_with(name='onion',
                                                     index='onion-v1')

        # Expected index delete calls
        es.indices.delete.assert_called_once_with(index='onion-v1')

        # Bulk
        bulk.assert_called_once_with(
            es, actions=ANY, index='onion-v1', chunk_size=2000, refresh=True
        )

        self.validate_actions(toAbsolute('__fixtures__/exp_socrata.ndjson'))

        logger.info.assert_any_call('Running index_ccdb with')
        logger.info.assert_any_call('Deleting and recreating onion-v1')
        logger.info.assert_any_call(
            'Loading data into onion-v1 with doc_type complaint'
        )
        logger.info.assert_any_call('chunk retrieved, now bulk load')
        logger.info.assert_any_call('1,001 records indexed, total = 1,001')
        logger.info.assert_any_call('Adding alias onion for index onion-v1')

    @freeze_time("2019-09-09")
    @patch('complaints.ccdb.index_ccdb.format_timestamp_local')
    @patch('complaints.ccdb.index_ccdb.bulk')
    @patch('complaints.ccdb.index_ccdb.get_es_connection')
    @patch('complaints.ccdb.index_ccdb.setup_logging')
    def test_main_happy_path_s3(self, logger_setup, es_conn, bulk, local_time):
        logger = Mock()
        logger_setup.return_value = logger

        es = Mock()
        es.indices.exists_alias.return_value = False
        es_conn.return_value = es

        bulk.side_effect = self.capture_actions

        # GMT: Monday, September 9, 2019 4:00:00 AM
        # EDT: Monday, September 9, 2019 12:00:00 AM
        local_time.return_value = 1568001600

        self.optional[-1] = toAbsolute('__fixtures__/from_s3.ndjson')
        self.optional.append('--metadata')
        self.optional.append(toAbsolute('__fixtures__/metadata.json'))

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            sut.main()

        # Expected index create calls
        es.indices.create.assert_any_call(index='onion-v1', ignore=400)
        es.indices.create.assert_any_call(index='onion-v2', ignore=400)
        es.indices.create.assert_any_call(index='onion-v1', body=ANY)

        # Expected index put_alias calls
        es.indices.put_alias.assert_called_once_with(name='onion',
                                                     index='onion-v1')

        # Expected index delete calls
        es.indices.delete.assert_called_once_with(index='onion-v1')

        # Bulk
        bulk.assert_called_once_with(
            es, actions=ANY, index='onion-v1', chunk_size=2000, refresh=True
        )

        self.validate_actions(toAbsolute('__fixtures__/exp_s3.ndjson'))

        logger.info.assert_any_call('Deleting and recreating onion-v1')
        logger.info.assert_any_call(
            'Loading data into onion-v1 with doc_type complaint'
        )
        logger.info.assert_any_call('chunk retrieved, now bulk load')
        logger.info.assert_any_call('1,001 records indexed, total = 1,001')
        logger.info.assert_any_call('Adding alias onion for index onion-v1')

    @patch('complaints.ccdb.index_ccdb.bulk')
    @patch('complaints.ccdb.index_ccdb.get_es_connection')
    @patch('complaints.ccdb.index_ccdb.setup_logging')
    def test_main_transport_error(self, logger_setup, es_conn, bulk):
        from elasticsearch import TransportError

        logger = Mock()
        logger_setup.return_value = logger

        es = Mock()
        es.indices.exists_alias.return_value = False
        es_conn.return_value = es

        bulk.side_effect = TransportError(404, 'oops')

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            with self.assertRaises(SystemExit):
                sut.main()

        # Rollback
        es.indices.put_alias.assert_called_once_with(name='onion',
                                                     index='onion-v2')

        self.assertEqual(logger.error.call_count, 1)

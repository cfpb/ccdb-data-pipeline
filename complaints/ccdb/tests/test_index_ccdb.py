import unittest
from unittest.mock import Mock

import complaints.ccdb.index_ccdb as sut


def toAbsolute(relative):
    import os

    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, relative)


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------


class TestIndexCCDB(unittest.TestCase):

    def test_update_indexes_in_alias__happy_path(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [True, True]
        expected = {
            "actions": [
                {"remove": {"index": "baz", "alias": "foo"}},
                {"add": {"index": "bar", "alias": "foo"}},
            ]
        }

        sut.update_indexes_in_alias(es, "foo", "baz", "bar")
        es.indices.update_aliases.assert_called_once_with(body=expected)

    def test_update_indexes_in_alias__no_aliases(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [False]
        sut.update_indexes_in_alias(es, "foo", "baz", "bar")
        es.indices.put_alias.assert_called_once_with(name="foo", index="bar")

    def test_update_indexes_in_alias__no_backup(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [True, False]
        expected = {"actions": [{"add": {"index": "bar", "alias": "foo"}}]}

        sut.update_indexes_in_alias(es, "foo", "baz", "bar")
        es.indices.update_aliases.assert_called_once_with(body=expected)

    # -------------------------------------------------------------------------

    def test_swap_backup_index__happy_path(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [True, True]
        a, b = sut.swap_backup_index(es, "foo", "bar", "baz")
        self.assertEqual(a, "baz")
        self.assertEqual(b, "bar")

    def test_swap_backup_index__no_alias(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [False]
        a, b = sut.swap_backup_index(es, "foo", "bar", "baz")
        self.assertEqual(a, "bar")
        self.assertEqual(b, "baz")

    def test_swap_backup_index__no_primary(self):
        es = Mock()
        es.indices.exists_alias.side_effect = [True, False]
        a, b = sut.swap_backup_index(es, "foo", "bar", "baz")
        self.assertEqual(a, "bar")
        self.assertEqual(b, "baz")

    # -------------------------------------------------------------------------

    def test_load_json_happy(self):
        fileName = toAbsolute("../../settings.json")
        actual = sut.load_json(fileName)
        self.assertIsNotNone(actual)

    def test_load_json_fail(self):
        fileName = toAbsolute("../../tests/__fixtures__/ccdb.ndjson")
        with self.assertRaises(SystemExit):
            sut.load_json(fileName)

    # -------------------------------------------------------------------------

    def test_yield_chunked_docs(self):
        def mock_data_fn(data):
            for x in data:
                yield x

        data = ["foo", "bar", "baz", "qaz", "quux"]
        gen = sut.yield_chunked_docs(mock_data_fn, data, 2)

        actual = next(gen)
        self.assertEqual(actual, ["foo", "bar"])
        actual = next(gen)
        self.assertEqual(actual, ["baz", "qaz"])
        rest = [x for x in gen]
        self.assertEqual(rest, [["quux"]])


class TestMain(unittest.TestCase):
    def setUp(self):
        self.optional = [
            "--es-host",
            "www.example.com",
            "--index-name",
            "onion",
            "--dataset",
            toAbsolute("__fixtures__/from_s3.ndjson"),
        ]
        self.actual_file = toAbsolute("__fixtures__/actual.json")

    def tearDown(self):
        import os

        try:
            os.remove(self.actual_file)
        except Exception:
            pass

    def capture_actions(self, *args, **kwargs):
        import io
        import json

        with io.open(self.actual_file, mode="w", encoding="utf-8") as f:
            for action in kwargs["actions"]:
                f.write(json.dumps(action, ensure_ascii=False))
                f.write("\n")

        return (1001, 99)

    def validate_actions(self, expected_file):
        import io
        import json

        self.maxDiff = None

        with io.open(self.actual_file, "r", encoding="utf-8") as f:
            actuals = [line for line in f]

        with io.open(expected_file, "r", encoding="utf-8") as f:
            expecteds = [line for line in f]

        assert len(actuals) == len(expecteds)

        for i, act in enumerate(actuals):
            actual = json.loads(act)
            expected = json.loads(expecteds[i])
            self.assertDictEqual(expected, actual)

import os
import unittest

import common.csv2json as sut
from common.tests import build_argv, captured_output, validate_json


def fixtureToAbsolute(fixture_file):
    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, '__fixtures__', fixture_file)


# -------------------------------------------------------------------------
# Test Classes

class TestMain(unittest.TestCase):
    def setUp(self):
        self.actual_file = fixtureToAbsolute('actual.')
        self.optional = [
            '--heartbeat', '2',
            '--limit', '3'
        ]
        self.positional = [
            fixtureToAbsolute('utf-8.csv'),
            self.actual_file
        ]

    def tearDown(self):
        os.remove(self.actual_file)

    def test_json(self):
        argv = build_argv(self.optional, self.positional)

        with captured_output(argv) as (out, err):
            sut.main()

        validate_json(self.actual_file, fixtureToAbsolute('utf-8.json'))

        actual_print = out.getvalue().strip()
        self.assertEqual('2 rows processed', actual_print)

    def test_ndjson(self):
        self.optional.extend(['--json-format', 'NDJSON'])
        argv = build_argv(self.optional, self.positional)

        with captured_output(argv) as (out, err):
            sut.main()

        validate_json(self.actual_file, fixtureToAbsolute('utf-8.ndjson'))

        actual_print = out.getvalue().strip()
        self.assertEqual('2 rows processed', actual_print)

    def test_switch_fields(self):
        self.optional.extend(
            ['--fields', fixtureToAbsolute('fields-good.txt')]
        )
        argv = build_argv(self.optional, self.positional)

        with captured_output(argv) as (out, err):
            sut.main()

        validate_json(self.actual_file,
                      fixtureToAbsolute('utf-8-switched.json'))

    def test_switch_fields_too_many(self):
        self.optional.extend(
            ['--fields', fixtureToAbsolute('fields-bad.txt')]
        )
        argv = build_argv(self.optional, self.positional)

        with self.assertRaises(SystemExit) as ex:
            with captured_output(argv) as (out, err):
                sut.main()

        actual_print = err.getvalue().strip()
        self.assertIn('has 4 fields.  Expected 3', actual_print)

        # assert exit code
        self.assertEqual(ex.exception.code, 2)

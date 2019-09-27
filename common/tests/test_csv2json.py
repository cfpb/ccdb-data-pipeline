from __future__ import unicode_literals
import common.csv2json as sut
import os
import sys
import unittest
from common.tests import captured_output, validate_json

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


def fixtureToAbsolute(fixture_file):
    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, '__fixtures__', fixture_file)


# -------------------------------------------------------------------------
# Test Classes

class TestMain(unittest.TestCase):
    def setUp(self):
        self.actual_file = fixtureToAbsolute('actual.')

        self.testargs = [
            'prog',
            '--heartbeat', '2',
            '--limit', '3',
            fixtureToAbsolute('utf-8.csv'),
            self.actual_file
        ]

    def tearDown(self):
        try:
            os.remove(self.actual_file)
        except Exception:
            pass

    def test_json(self):
        with captured_output() as (out, err):
            with patch.object(sys, 'argv', self.testargs):
                sut.main()

        validate_json(self.actual_file, fixtureToAbsolute('utf-8.json'))

        actual_print = out.getvalue().strip()
        self.assertEqual('2 rows processed', actual_print)

    def test_ndjson(self):
        self.testargs[1:1] = ['--json-format', 'NDJSON']

        with captured_output() as (out, err):
            with patch.object(sys, 'argv', self.testargs):
                sut.main()

        validate_json(self.actual_file, fixtureToAbsolute('utf-8.ndjson'))

        actual_print = out.getvalue().strip()
        self.assertEqual('2 rows processed', actual_print)

    def test_switch_fields(self):
        self.testargs[1:1] = ['--fields', fixtureToAbsolute('fields-good.txt')]

        with captured_output() as (out, err):
            with patch.object(sys, 'argv', self.testargs):
                sut.main()

        validate_json(self.actual_file,
                      fixtureToAbsolute('utf-8-switched.json'))

    def test_switch_fields_too_many(self):
        self.testargs[1:1] = ['--fields', fixtureToAbsolute('fields-bad.txt')]

        with captured_output() as (out, err):
            with patch.object(sys, 'argv', self.testargs):
                sut.main()

        # Still processes!
        validate_json(self.actual_file, fixtureToAbsolute('utf-8.json'))

        actual_print = err.getvalue().strip()
        self.assertIn('has 4 fields.  Expected 3', actual_print)

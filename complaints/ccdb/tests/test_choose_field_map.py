import os
import unittest

import complaints.ccdb.choose_field_map as sut
from common.tests import build_argv, captured_output, validate_files


def fieldsToAbsolute(mapping_file):
    # where is _this_ file? and one level up
    thisScriptDir = os.path.dirname(os.path.dirname(__file__))

    return os.path.join(thisScriptDir, 'fields-s3', mapping_file)


def fixtureToAbsolute(fixture_file):
    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, '__fixtures__', fixture_file)

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------


class TestMain(unittest.TestCase):
    def setUp(self):
        self.actual_file = fixtureToAbsolute('a.txt')
        self.positional = [
            None,
            self.actual_file
        ]

    def tearDown(self):
        try:
            os.remove(self.actual_file)
        except Exception:
            pass

    def test_v1_intake_json(self):
        self.positional[0] = fixtureToAbsolute('v1-intake.csv')
        argv = build_argv(positional=self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        validate_files(self.actual_file, fieldsToAbsolute('v1-json.txt'))

        actual_print = out.getvalue().strip()
        self.assertEqual('Using "v1-json.txt" for field mapping', actual_print)

    def test_v1_intake_csv(self):
        self.positional[0] = fixtureToAbsolute('v1-intake.csv')
        optional = [
            '--target-format', 'CSV'
        ]
        argv = build_argv(optional, self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        validate_files(self.actual_file, fieldsToAbsolute('v1-csv.txt'))

        actual_print = out.getvalue().strip()
        self.assertEqual('Using "v1-csv.txt" for field mapping', actual_print)

    def test_v1_public(self):
        self.positional[0] = fixtureToAbsolute('v1-public.csv')
        argv = build_argv(positional=self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        validate_files(self.actual_file, fieldsToAbsolute('v1-json.txt'))

        actual_print = out.getvalue().strip()
        self.assertEqual('Using "v1-json.txt" for field mapping', actual_print)

    def test_v2_intake(self):
        self.positional[0] = fixtureToAbsolute('v2-intake.csv')
        argv = build_argv(positional=self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        validate_files(self.actual_file, fieldsToAbsolute('v2-json.txt'))

        actual_print = out.getvalue().strip()
        self.assertEqual('Using "v2-json.txt" for field mapping', actual_print)

    def test_v2_public(self):
        self.positional[0] = fixtureToAbsolute('v2-public.csv')
        argv = build_argv(positional=self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        validate_files(self.actual_file, fieldsToAbsolute('v2-json.txt'))

        actual_print = out.getvalue().strip()
        self.assertEqual('Using "v2-json.txt" for field mapping', actual_print)

    def test_bad_input(self):
        self.positional[0] = fixtureToAbsolute('complaints-subset.csv')
        argv = build_argv(positional=self.positional)
        with self.assertRaises(SystemExit) as ex:
            with captured_output(argv) as (out, err):
                sut.main()

        self.assertEqual(ex.exception.code, 2)

        console_output = err.getvalue()
        self.assertIn('Unknown field set', console_output)

    def test_bad_format_argument(self):
        self.positional[0] = fixtureToAbsolute('v1-intake.csv')
        optional = [
            '--target-format', 'tsv'
        ]
        argv = build_argv(optional, self.positional)
        with self.assertRaises(SystemExit) as ex:
            with captured_output(argv) as (out, err):
                sut.main()

        self.assertEqual(ex.exception.code, 2)

        console_output = err.getvalue()
        self.assertIn('usage: choose_field_map', console_output)
        self.assertIn('--target-format: invalid choice', console_output)

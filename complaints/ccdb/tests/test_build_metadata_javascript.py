import io
import os
import unittest
from unittest.mock import mock_open, patch

import complaints.ccdb.build_metadata_javascript as sut
from common.tests import build_argv, captured_output, validate_files


def fixtureToAbsolute(fixture_file):
    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, '__fixtures__', fixture_file)


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class TestMain(unittest.TestCase):
    def setUp(self):
        self.actual_file = fixtureToAbsolute('a.tmp')
        self.positional = [
            fixtureToAbsolute('metadata_public.json'),
            self.actual_file
        ]

    def tearDown(self):
        try:
            os.remove(self.actual_file)
        except Exception:
            pass

    def test_main_happy_path(self):
        argv = build_argv(positional=self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        validate_files(self.actual_file, fixtureToAbsolute('metadata.js'))

        console_output = out.getvalue()
        self.assertEqual(console_output, '')

    def test_bad_input(self):
        self.positional[0] = fixtureToAbsolute('exp_s3.ndjson')

        with self.assertRaises(SystemExit) as ex:
            argv = build_argv(positional=self.positional)
            with captured_output(argv) as (out, err):
                sut.main()

        self.assertEqual(ex.exception.code, 2)

        console_output = err.getvalue()
        self.assertIn('exp_s3.ndjson', console_output)
        self.assertIn('is not a valid JSON document', console_output)

    def test_cant_write(self):
        m = mock_open()
        m.side_effect = IOError

        with self.assertRaises(SystemExit) as ex:
            with patch.object(io, 'open', m):
                with captured_output([]) as (out, err):
                    sut.save_javascript({}, 'foo')

        self.assertEqual(ex.exception.code, 5)

        console_output = err.getvalue()
        self.assertIn("Unable to write 'foo'", console_output)

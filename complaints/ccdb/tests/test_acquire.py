import os
import unittest
from datetime import datetime
from unittest.mock import ANY, Mock, patch

import pytz

import complaints.ccdb.acquire as sut
from common.tests import build_argv, captured_output, make_configargs


def toAbsolute(relative):
    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, relative)


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class TestProgress(unittest.TestCase):
    def test_callback(self):
        options = make_configargs({
            'outfile': 'foo.bar'
        })
        instance = sut.ProgressPercentage(options)
        with captured_output([]) as (out, err):
            instance(100)

        self.assertEqual(out.getvalue(), '\rfoo.bar  100 bytes')


class TestMain(unittest.TestCase):
    def setUp(self):
        self.actual_file = toAbsolute('__fixtures__/a.tmp')
        self.optional = [
            '--s3-bucket', 'foo',
            '--s3-key', 'bar',
            '-o', self.actual_file
        ]
        self.timestamp = 1567987200  # Midnight 2019-09-09 UTC

    def tearDown(self):
        try:
            os.remove(self.actual_file)
        except Exception:
            pass

    @patch('complaints.ccdb.acquire.boto3')
    def test_main_happy_path_download(self, boto3):
        bucket = Mock()
        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        self.optional.insert(0, '--dump-config')

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            sut.main()

        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')
        bucket.download_file.assert_called_once_with(
            'bar', self.actual_file, Callback=ANY
        )

        console_output = out.getvalue()
        self.assertIn('Command Line Args:', console_output)
        self.assertIn('Defaults:', console_output)
        self.assertIn('--timezone:', console_output)

    @patch('complaints.ccdb.acquire.boto3')
    def test_main_happy_path_check_latest(self, boto3):
        dataset = make_configargs({
            'last_modified': datetime.fromtimestamp(self.timestamp, pytz.utc)
        })
        bucket = Mock()
        bucket.Object.return_value = dataset

        s3 = Mock()
        s3.Bucket.return_value = bucket

        boto3.resource.return_value = s3

        self.optional.insert(0, '--check-latest')

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            sut.main()

        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')
        bucket.Object.assert_called_once_with('bar')

        stat = os.stat(self.actual_file)
        self.assertEqual(self.timestamp, stat.st_mtime)

    @patch('complaints.ccdb.acquire.boto3')
    def test_main_happy_path_check_latest_no_new_data(self, boto3):
        dataset = make_configargs({
            'last_modified': datetime.fromtimestamp(self.timestamp, pytz.utc)
        })
        bucket = Mock()
        bucket.Object.return_value = dataset

        s3 = Mock()
        s3.Bucket.return_value = bucket

        boto3.resource.return_value = s3

        self.optional.insert(0, '--check-latest')

        # Make sure the file exists and reflects the expected timestamp
        open(self.actual_file, 'a').close()
        os.utime(self.actual_file, (self.timestamp, self.timestamp))

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            sut.main()

        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')
        bucket.Object.assert_called_once_with('bar')

        self.assertTrue(True, '\nNo new data set since 08:00 ' +
                              'PM Sunday, September 08, 2019\n' in
                              out.getvalue())

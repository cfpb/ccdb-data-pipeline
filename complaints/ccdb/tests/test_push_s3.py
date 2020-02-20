import os
import unittest
from unittest.mock import ANY, Mock, patch

import complaints.ccdb.push_s3 as sut
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
            'infile': 'foo.bar'
        })
        instance = sut.ProgressPercentage(options)
        with captured_output([]) as (out, err):
            instance(100)

        self.assertEqual(out.getvalue(), '\rfoo.bar  100 bytes')


class TestMain(unittest.TestCase):
    def setUp(self):
        self.optional = [
            '--s3-bucket', 'foo',
            '--s3-folder', 'bar'
        ]
        self.positional = [
            toAbsolute('__fixtures__/from_s3.ndjson')
        ]

    @patch('complaints.ccdb.push_s3.boto3')
    def test_main_happy_path_ndjson(self, boto3):
        bucket = Mock()
        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        argv = build_argv(self.optional, self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')
        bucket.upload_file.assert_called_once_with(
            'from_s3.ndjson.zip', 'bar/from_s3.ndjson.zip', Callback=ANY
        )

    @patch('complaints.ccdb.push_s3.boto3')
    def test_main_happy_path_json(self, boto3):
        bucket = Mock()
        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        self.optional.insert(0, '--dump-config')
        self.positional = [
            toAbsolute('__fixtures__/from_s3.json')
        ]

        argv = build_argv(self.optional, self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')
        bucket.upload_file.assert_called_once_with(
            'from_s3.json.zip', 'bar/from_s3.json.zip', Callback=ANY
        )

        console_output = out.getvalue()
        self.assertIn('Command Line Args:', console_output)
        self.assertNotIn('Defaults:', console_output)
        self.assertNotIn('Environment Variables:', console_output)

    @patch('complaints.ccdb.push_s3.boto3')
    def test_main_happy_path_nozip(self, boto3):
        bucket = Mock()
        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        self.optional.append('--no-zip')
        argv = build_argv(self.optional, self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')
        bucket.upload_file.assert_called_once_with(
            self.positional[0], 'bar/from_s3.ndjson', Callback=ANY
        )

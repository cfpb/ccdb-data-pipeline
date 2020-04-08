import os
import unittest
from unittest.mock import Mock, patch

import complaints.ccdb.verify_s3 as sut
from common.tests import build_argv, captured_output, make_configargs


def toAbsolute(relative):
    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)
    return os.path.join(thisScriptDir, relative)


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------


class TestMain(unittest.TestCase):
    def setUp(self):
        self.optional = [
            '--s3-bucket', 'foo',
            '--s3-folder', 'bar'
        ]

        self.json_size_file = toAbsolute('__fixtures__/prev_json_size.txt')
        self.cache_size_file = toAbsolute('__fixtures__/prev_cache_size.txt')

        self.positional = [
            'json_data.json',
            self.json_size_file,
            self.cache_size_file
        ]

    def tearDown(self):
        with open(self.json_size_file, 'w+') as f:
            f.write(str(0))
        with open(self.cache_size_file, 'w+') as f:
            f.write(str(0))

    @patch('complaints.ccdb.verify_s3.boto3')
    def test_verify_happy_path(self, boto3):
        dataset = make_configargs({
            'content_length': 180
        })
        bucket = Mock()
        bucket.Object.return_value = dataset

        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        self.optional.insert(0, '--dump-config')
        argv = build_argv(self.optional, self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        # assert calls
        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')

        # assert file size update
        with open(self.json_size_file, 'r') as f:
            prev_json_size = int(f.read())

        self.assertTrue(prev_json_size == 180)

        # assert cache size update
        with open(self.cache_size_file, 'r') as f:
            prev_cache_size = int(f.read())

        self.assertTrue(prev_cache_size != 0)

    @patch('complaints.ccdb.verify_s3.boto3')
    def test_verify_file_verify_failure(self, boto3):
        dataset = make_configargs({
            'content_length': -1
        })
        bucket = Mock()
        bucket.Object.return_value = dataset

        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        with self.assertRaises(SystemExit) as ex:
            argv = build_argv(self.optional, self.positional)
            with captured_output(argv) as (out, err):
                sut.main()

        # assert calls
        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')

        # assert exit code
        self.assertEqual(ex.exception.code, 2)

    @patch('complaints.ccdb.verify_s3.boto3')
    def test_verify_json_file_invalid(self, boto3):
        invalid_count_file = \
            toAbsolute('__fixtures__/prev_json_size_invalid.txt')

        test_positional = [
            'json_data.json',
            invalid_count_file,
            self.cache_size_file
        ]

        dataset = make_configargs({
            'content_length': 1
        })
        bucket = Mock()
        bucket.Object.return_value = dataset

        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        argv = build_argv(self.optional, test_positional)
        with captured_output(argv) as (out, err):
            sut.main()

        # assert json size update
        with open(invalid_count_file, 'r') as f:
            prev_json_size = int(f.read())

        self.assertTrue(prev_json_size != 0)

        # Clean up
        with open(invalid_count_file, 'w+') as f:
            f.write(str('Invalid'))

    @patch('complaints.ccdb.verify_s3.boto3')
    def test_verify_cache_verify_failure(self, boto3):
        dataset = make_configargs({
            'content_length': 1
        })
        bucket = Mock()
        bucket.Object.return_value = dataset

        # set up intentionally large cache size
        with open(self.cache_size_file, 'w+') as f:
            f.write(str(99999999))

        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        with self.assertRaises(SystemExit) as ex:
            argv = build_argv(self.optional, self.positional)
            with captured_output(argv) as (out, err):
                sut.main()

        # assert calls
        boto3.resource.assert_called_once_with('s3')
        s3.Bucket.assert_called_once_with('foo')

        # assert exit code
        self.assertEqual(ex.exception.code, 2)

    @patch('complaints.ccdb.verify_s3.boto3')
    def test_verify_cache_file_invalid(self, boto3):
        invalid_count_file = \
            toAbsolute('__fixtures__/prev_cache_size_invalid.txt')

        test_positional = [
            'json_data.json',
            self.json_size_file,
            invalid_count_file
        ]

        dataset = make_configargs({
            'content_length': 1
        })
        bucket = Mock()
        bucket.Object.return_value = dataset

        s3 = Mock()
        s3.Bucket.return_value = bucket
        boto3.resource.return_value = s3

        argv = build_argv(self.optional, test_positional)
        with captured_output(argv) as (out, err):
            sut.main()

        # assert json size update
        with open(invalid_count_file, 'r') as f:
            prev_cache_size = int(f.read())

        self.assertTrue(prev_cache_size != 0)

        # Clean up
        with open(invalid_count_file, 'w+') as f:
            f.write(str('Invalid'))

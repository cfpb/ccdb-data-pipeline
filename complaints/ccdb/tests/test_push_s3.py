import os
import unittest
from unittest.mock import ANY, Mock, patch

import complaints.ccdb.push_s3 as sut
from common.tests import build_argv, captured_output


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
        self.positional = [
            toAbsolute('__fixtures__/from_s3.ndjson')
        ]

    @patch('complaints.ccdb.push_s3.boto3')
    def test_main_happy_path(self, boto3):
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


if __name__ == '__main__':
    unittest.main()

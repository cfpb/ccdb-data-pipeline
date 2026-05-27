import unittest
from unittest.mock import mock_open, patch

import common.s3_utils as s3_utils


class TestS3Utils(unittest.TestCase):
    @patch("common.s3_utils.boto3.resource")
    def test_download_file(self, mock_resource):
        # Setup mock
        mock_s3 = mock_resource.return_value
        mock_bucket = mock_s3.Bucket.return_value

        s3_utils.download_file("my-bucket", "path/to/key.zip", "local.zip")

        # Verify S3 call
        mock_s3.Bucket.assert_called_with("my-bucket")
        mock_bucket.download_file.assert_called_with("path/to/key.zip", "local.zip")

    @patch("common.s3_utils.boto3.resource")
    def test_upload_file(self, mock_resource):
        mock_s3 = mock_resource.return_value
        mock_bucket = mock_s3.Bucket.return_value

        s3_utils.upload_file("my-bucket", "path/to/key.zip", "local.zip")

        mock_bucket.upload_file.assert_called_with("local.zip", "path/to/key.zip")

    def test_ymd_conversion(self):
        iso_date = "2023-12-25T12:00:00"
        expected = "2023-12-25"
        self.assertEqual(s3_utils.ymd(iso_date), expected)

    @patch("common.s3_utils.ZipFile")
    @patch("common.s3_utils.write_and_zip")
    def test_append_to_zip(self, mock_write_and_zip, mock_zipfile):
        # Mocking ZipFile context manager
        instance = mock_zipfile.return_value.__enter__.return_value

        s3_utils.append_to_zip("data.zip", "new_data.csv")

        # Ensure it extracts before appending
        instance.extractall.assert_called_with(".")
        mock_write_and_zip.assert_called_with("new_data.csv", "data", "a")

    @patch("common.s3_utils.csv.reader")
    @patch("common.s3_utils.csv.writer")
    @patch("common.s3_utils.ZipFile")
    @patch(
        "builtins.open", new_callable=mock_open, read_data="header,data\n2023-01-01,val"
    )
    def test_write_and_zip(self, mock_file, mock_zip, mock_csv_writer, mock_csv_reader):
        mock_row = ["2023-01-01T10:00:00"] + [""] * 11 + ["2023-02-02T10:00:00", "True"]
        mock_csv_reader.return_value = iter([["header1", "header2"], mock_row])

        writer_instance = mock_csv_writer.return_value

        s3_utils.write_and_zip("in.csv", "out", mode="w", header=["H1", "H2"])

        writer_instance.writerow.assert_any_call(["H1", "H2"])

        # Check if dates were converted
        args, _ = writer_instance.writerow.call_args
        self.assertEqual(args[0][0], "2023-01-01")
        self.assertEqual(args[0][12], "2023-02-02")

    @patch("common.s3_utils.download_file")
    @patch("common.s3_utils.append_to_zip")
    @patch("common.s3_utils.upload_file")
    def test_update_zipped_archive(self, mock_upload, mock_append, mock_download):
        s3_utils.update_zipped_archive("my-bucket", "folder/test.zip", "data.csv")

        mock_download.assert_called_once()
        mock_append.assert_called_with("test.zip", "data.csv")
        mock_upload.assert_called_once()

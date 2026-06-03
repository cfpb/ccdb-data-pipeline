import unittest
from unittest.mock import MagicMock, mock_open, patch

# Import the module under test
import common.s3_utils as s3_utils


class TestS3Utils(unittest.TestCase):
    @patch("common.s3_utils.boto3.resource")
    def test_download_file(self, mock_boto_resource):
        mock_s3 = MagicMock()
        mock_bucket = MagicMock()
        mock_boto_resource.return_value = mock_s3
        mock_s3.Bucket.return_value = mock_bucket

        s3_utils.download_file("my-bucket", "my-prefix/", "data.zip")

        mock_boto_resource.assert_called_once_with("s3")
        mock_s3.Bucket.assert_called_once_with("my-bucket")
        mock_bucket.download_file.assert_called_once_with(
            "my-prefix/data.zip", "data.zip"
        )

    @patch("common.s3_utils.boto3.resource")
    def test_upload_file(self, mock_boto_resource):
        mock_s3 = MagicMock()
        mock_bucket = MagicMock()
        mock_boto_resource.return_value = mock_s3
        mock_s3.Bucket.return_value = mock_bucket

        s3_utils.upload_file("my-bucket", "my-prefix/", "data.zip")

        mock_boto_resource.assert_called_once_with("s3")
        mock_s3.Bucket.assert_called_once_with("my-bucket")
        mock_bucket.upload_file.assert_called_once_with(
            "data.zip", "my-prefix/data.zip"
        )

    def test_ymd_conversion(self):
        iso_str = "2026-06-01T13:45:00"
        self.assertEqual(s3_utils.ymd(iso_str), "2026-06-01")

    @patch("common.s3_utils.ZipFile")
    def test_make_zip(self, mock_zipfile):
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        s3_utils.make_zip("test.csv", "test.zip")

        mock_zip_instance.write.assert_called_once_with("test.csv")

    @patch("common.s3_utils.subprocess.run")
    def test_make_json(self, mock_sub_run):
        result = s3_utils.make_json("archive.csv")

        self.assertEqual(result, "archive.json")
        mock_sub_run.assert_called_once_with(
            [
                "python",
                "common/csv2json.py",
                "--json-format",
                "JSON",
                "--fields",
                "complaints/ccdb/fields-s3/v1-json.txt",
                "archive.csv",
                "archive.json",
            ],
            check=True,
        )

    @patch("common.s3_utils.ymd")
    @patch("common.s3_utils.csv.writer")
    @patch("common.s3_utils.csv.reader")
    def test_write_csv(self, mock_csv_reader, mock_csv_writer, mock_ymd):
        # Setup mock behavior
        mock_reader_instance = MagicMock()
        mock_reader_instance.__next__.return_value = ["header1", "header2"]
        mock_reader_instance.__iter__.return_value = [
            [
                "2026-01-01T00:00:00",
                "data",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "2026-01-02T00:00:00",
            ]
        ]
        mock_csv_reader.return_value = mock_reader_instance

        mock_writer_instance = MagicMock()
        mock_csv_writer.return_value = mock_writer_instance

        mock_ymd.side_effect = ["2026-01-01", "2026-01-02"]

        # Mock the open call for both files
        with patch("builtins.open", mock_open()):
            s3_utils.write_csv("in.csv", "out.csv", header=["h1", "h2"])

        mock_writer_instance.writerow.assert_any_call(["h1", "h2"])
        mock_writer_instance.writerow.assert_any_call(
            ["2026-01-01", "data", "", "", "", "", "", "", "", "", "", "", "2026-01-02"]
        )

    @patch("common.s3_utils.make_zip")
    @patch("common.s3_utils.make_json")
    @patch("common.s3_utils.os.replace")
    @patch("common.s3_utils.csv.writer")
    @patch("common.s3_utils.csv.reader")
    @patch("common.s3_utils.ZipFile")
    def test_append_to_zips(
        self,
        mock_zipfile,
        mock_reader,
        mock_writer,
        mock_replace,
        mock_make_json,
        mock_make_zip,
    ):
        # Simulating Zip extraction
        mock_zip_ref = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_ref

        # Mock CSV readers for internal context managers
        mock_orig_reader = MagicMock()
        mock_orig_reader.__next__.return_value = ["header"]
        # row[15] setup for de-duplication testing
        row_orig = [""] * 16
        row_orig[15] = "duplicate_id"
        mock_orig_reader.__iter__.return_value = [row_orig]

        mock_append_reader = MagicMock()
        mock_append_reader.__next__.return_value = ["header"]
        row_append = [""] * 16
        row_append[15] = "duplicate_id"
        mock_append_reader.__iter__.return_value = [row_append]

        mock_reader.side_effect = [mock_orig_reader, mock_append_reader]

        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance

        mock_make_json.return_value = "archive.json"

        with patch("builtins.open", mock_open()):
            s3_utils.append_to_zips("archive.zip", "new_data.csv")

        mock_zip_ref.extractall.assert_called_once_with(".")
        mock_replace.assert_called_once_with("temp_file", "archive")
        mock_make_json.assert_called_once_with("archive")

        # Ensure it zipped both the CSV and JSON variations
        mock_make_zip.assert_any_call("archive", "archive.zip")
        mock_make_zip.assert_any_call("archive.json", "archive.json.zip")

    @patch("common.s3_utils.upload_file")
    @patch("common.s3_utils.append_to_zips")
    @patch("common.s3_utils.download_file")
    def test_update_zipped_archives(self, mock_download, mock_append, mock_upload):
        s3_utils.update_zipped_archives("bucket", "prefix/", "base", "new.csv")

        mock_download.assert_called_once_with("bucket", "prefix/", "base.csv.zip")
        mock_append.assert_called_once_with("base.csv.zip", "new.csv")
        mock_upload.assert_any_call("bucket", "prefix/", "base.csv.zip")
        mock_upload.assert_any_call("bucket", "prefix/", "base.json.zip")

    @patch("common.s3_utils.upload_file")
    @patch("common.s3_utils.make_zip")
    @patch("common.s3_utils.make_json")
    @patch("common.s3_utils.write_csv")
    @patch("common.s3_utils.os.path.abspath")
    def test_create_zipped_archives(
        self, mock_abspath, mock_write_csv, mock_make_json, mock_make_zip, mock_upload
    ):
        mock_abspath.return_value = "/root/common/s3_utils.py"
        mock_make_json.return_value = "base.json"

        # Mock the header file reading context manager
        with patch("builtins.open", mock_open(read_data="col1\ncol2")):
            s3_utils.create_zipped_archives("bucket", "prefix/", "base", "new.csv")

        mock_write_csv.assert_called_once_with(
            "new.csv", "base.csv", header=["col1", "col2"]
        )
        mock_make_json.assert_called_once_with("base.csv")
        mock_make_zip.assert_any_call("base.csv", "base.csv.zip")
        mock_make_zip.assert_any_call("base.json", "base.json.zip")
        mock_upload.assert_any_call("bucket", "prefix/", "base.csv.zip")
        mock_upload.assert_any_call("bucket", "prefix/", "base.json.zip")


if __name__ == "__main__":
    unittest.main()

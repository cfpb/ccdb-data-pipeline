import os
import tempfile
from unittest import TestCase, mock

from salesforce.export import export_to_csv


class ExportTests(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def write_page(self, name, content):
        path = os.path.join(self.tmpdir.name, name)
        with open(path, "w") as f:
            f.write(content)
        return {"locator": "", "number_of_records": 0, "file": path}

    @mock.patch("salesforce.export.Salesforce")
    def test_export_concatenates_pages_with_single_header(self, mock_sf):
        pages = [
            self.write_page("1.csv", '"A","B"\n"1","2"\n"3","4"\n'),
            self.write_page("2.csv", '"A","B"\n"5","6"\n'),
        ]
        mock_sf.return_value.bulk2.Case.download.return_value = pages

        output_file = os.path.join(self.tmpdir.name, "out.csv")
        export_to_csv("SELECT A, B FROM Case", output_file, "sid", "host")

        mock_sf.assert_called_once_with(session_id="sid", instance="host")
        download = mock_sf.return_value.bulk2.Case.download
        self.assertEqual(download.call_args.args, ("SELECT A, B FROM Case",))

        with open(output_file) as f:
            self.assertEqual(f.read(), '"A","B"\n"1","2"\n"3","4"\n"5","6"\n')

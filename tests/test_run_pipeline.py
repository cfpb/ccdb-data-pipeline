import os
import unittest

import run_pipeline as sut
from common.tests import build_argv, captured_output

try:
    from unittest.mock import patch, Mock, ANY
except ImportError:
    from mock import patch, Mock, ANY


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
            '-o', 'www.example.org',
            '-p', '9200',
            '-u', 'foo',
            '-a', 'bar',
            '-i', 'lizard'
        ]

    @patch('run_pipeline.test_index_growing')
    @patch('run_pipeline.Elasticsearch')
    @patch('run_pipeline.parse_json')
    @patch('run_pipeline.taxonomy_index')
    @patch('run_pipeline.ccdb_index')
    def test_main_happy_path(
        self, ccdb_index, taxonomy_index, parser, es_ctor, test_growing
    ):
        es = Mock()
        es_ctor.return_value = es

        argv = build_argv(self.optional)
        with captured_output(argv) as (out, err):
            sut.main()

        test_growing.assert_called_once_with(es, 'lizard-v1')

        parser.assert_called_once_with(
            'https://data.consumerfinance.gov/api/views/s6ew-h6mp/rows.json',
            'complaints/ccdb/ccdb_output.json',
            ANY
        )

        ccdb_index.index_json_data.assert_called_once_with(
            es, ANY, 'complaint',
            'complaints/settings.json',
            'complaints/ccdb/ccdb_mapping.json',
            'complaints/ccdb/ccdb_output.json',
            'lizard-v1', 'lizard-v2', 'lizard'
        )

        taxonomy_index.index_taxonomy.assert_called_once_with(
            es, ANY, 'complaints/taxonomy/taxonomy.txt', 'lizard'
        )


if __name__ == '__main__':
    unittest.main()

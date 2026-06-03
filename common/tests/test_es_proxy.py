import os
import unittest
from unittest.mock import patch

import common.es_proxy as sut

# -------------------------------------------------------------------------
# Test Classes


class TestEdges(unittest.TestCase):
    @patch("common.es_proxy.OpenSearch")
    @patch.dict(
        os.environ,
        {
            "ES_HOST": "www.example.org",
            "ES_PORT": "9222",
            "ES_USERNAME": "king",
            "ES_PASSWORD": "kong",
        },
    )
    def test_get_es_connection(self, mock_es):
        mock_es.return_value = "passed"

        actual = sut.get_es_connection()
        self.assertEqual(actual, "passed")
        mock_es.assert_called_once_with(
            "http://king:kong@www.example.org:9222", timeout=2000, use_ssl=False
        )

    @patch("common.es_proxy.OpenSearch")
    @patch.dict(
        os.environ,
        {
            "ES_HOST": "www.example.org",
            "ES_PORT": "443",
            "ES_USERNAME": "king!",
            "ES_PASSWORD": "kong",
        },
    )
    def test_get_es_connection_ssl(self, mock_es):
        mock_es.return_value = "passed"

        actual = sut.get_es_connection()
        self.assertEqual(actual, "passed")
        mock_es.assert_called_once_with(
            "http://king%21:kong@www.example.org:443", timeout=2000, use_ssl=True
        )

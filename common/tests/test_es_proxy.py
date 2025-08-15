import unittest
from unittest.mock import patch

import common.es_proxy as sut
from common.tests import make_configargs

# -------------------------------------------------------------------------
# Test Classes


class TestEdges(unittest.TestCase):
    @patch('common.es_proxy.Elasticsearch')
    def test_get_es_connection(self, mock_es):
        options = make_configargs({
            'es_host': 'www.example.org',
            'es_port': '9222',
            'es_username': 'king',
            'es_password': 'kong',
        })
        mock_es.return_value = 'passed'

        actual = sut.get_es_connection(options)
        self.assertEqual(actual, 'passed')
        mock_es.assert_called_once_with(
            'http://king:kong@www.example.org:9222',
            timeout=2000,
            use_ssl=False)

    @patch('common.es_proxy.Elasticsearch')
    def test_get_es_connection_ssl(self, mock_es):
        options = make_configargs({
            'es_host': 'www.example.org',
            'es_port': '443',
            'es_username': 'king!',
            'es_password': 'kong',
        })
        mock_es.return_value = 'passed'

        actual = sut.get_es_connection(options)
        self.assertEqual(actual, 'passed')
        mock_es.assert_called_once_with(
            'http://king%21:kong@www.example.org:443',
            timeout=2000,
            use_ssl=True)

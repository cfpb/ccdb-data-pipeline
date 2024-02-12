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
            'http://www.example.org:9222',
            http_auth=('king', 'kong'),
            timeout=2000,
            user_ssl=True)

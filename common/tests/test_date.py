import unittest

import common.date as sut

# -------------------------------------------------------------------------
# Test Classes


class TestEdges(unittest.TestCase):
    def test_unexpected_date_string(self):
        actual = sut.format_timestamp_local('01/23/2020')
        self.assertEqual(actual, 0)

    def test_date_string_that_passes_everywhere(self):
        actual = sut.format_timestamp_local('2019-09-09 00:00:00')
        self.assertGreaterEqual(actual, 1567987200)
        self.assertLessEqual(actual, 1568073600)

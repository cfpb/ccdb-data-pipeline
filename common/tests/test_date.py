import unittest

import common.date as sut

# -------------------------------------------------------------------------
# Test Classes


class TestEdges(unittest.TestCase):
    def test_unexpected_date_string(self):
        actual = sut.format_timestamp_local('01/23/2020')
        self.assertEqual(actual, 0)

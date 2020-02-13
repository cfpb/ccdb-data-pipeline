import unittest

import common.log as sut

# -------------------------------------------------------------------------
# Test Classes


class TestEdges(unittest.TestCase):
    def test_setup_logging(self):
        actual = sut.setup_logging('foo')
        self.assertIsNotNone(actual)

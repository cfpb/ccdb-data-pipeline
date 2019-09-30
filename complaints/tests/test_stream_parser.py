from __future__ import unicode_literals
import complaints.streamParser as sut
import os
import unittest
from common.tests import validate_json
from freezegun import freeze_time

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


def fixtureToAbsolute(fixture_file):
    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, '__fixtures__', fixture_file)


# -------------------------------------------------------------------------
# Test Classes

class TestMain(unittest.TestCase):
    def setUp(self):
        self.actual_file = fixtureToAbsolute('actual.json')

    def tearDown(self):
        try:
            os.remove(self.actual_file)
        except Exception:
            pass

    @freeze_time("2019-09-09")
    def test_json(self):
        logger = Mock()

        sut.parse_json_file(
            fixtureToAbsolute('socrata.json'),
            self.actual_file,
            logger
        )

        validate_json(self.actual_file, fixtureToAbsolute('ccdb.json'))

        logger.info.assert_any_call('Completed parsing input file')
        logger.info.assert_any_call('Processed 2972 lines, 2972 total')
        logger.info.assert_any_call('Closed output file')

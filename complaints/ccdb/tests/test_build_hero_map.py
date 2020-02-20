import os
import unittest

import complaints.ccdb.build_hero_map as sut
from common.tests import (
    build_argv, captured_output, make_configargs
)
from freezegun import freeze_time


def fixtureToAbsolute(fixture_file):
    # where is _this_ file?
    thisScriptDir = os.path.dirname(__file__)

    return os.path.join(thisScriptDir, '__fixtures__', fixture_file)


def assert_output_equal(actual_file, expected_file):
    import io
    import json

    with io.open(actual_file, 'r', encoding='utf-8') as f:
        actual = json.load(f)

    with io.open(expected_file, 'r', encoding='utf-8') as f:
        expected = json.load(f)

    assert len(actual) == len(expected)
    for i in range(len(expected)):
        assert actual[i] == expected[i]


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

@freeze_time("2020-01-01")
class TestMain(unittest.TestCase):
    def setUp(self):
        self.actual_file = fixtureToAbsolute('actual.')
        self.optional = [
            '--heartbeat', '100',
            '--limit', '280'
        ]
        self.positional = [
            fixtureToAbsolute('complaints-subset.csv'),
            self.actual_file
        ]

    def tearDown(self):
        os.remove(self.actual_file)

    def test_main_happy_path(self):
        argv = build_argv(self.optional, self.positional)
        with captured_output(argv) as (out, err):
            sut.main()

        assert_output_equal(
            self.actual_file, fixtureToAbsolute('exp_hero-map-3y.json')
        )

        actual_print = out.getvalue().strip()
        self.assertIn('Skipping "FOO"', actual_print)
        self.assertIn('Skipping ""', actual_print)
        self.assertIn('200 rows processed', actual_print)

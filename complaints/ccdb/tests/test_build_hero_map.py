import os
import unittest

import complaints.ccdb.build_hero_map as sut
from common.tests import build_argv, captured_output, make_configargs
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
        assert actual[i] == expected[i], expected[i]['name']


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class TestGetInterval(unittest.TestCase):
    def setUp(self):
        self.options = make_configargs({
            'interval': '3y'
        })

    @freeze_time("2020-01-01")
    def test_happy_path(self):
        (actual_min, actual_max) = sut.get_interval(self.options)
        self.assertEqual(actual_min, '2017-01-01')
        self.assertEqual(actual_max, '2020-01-01')

    @freeze_time("2020-02-29")
    def test_leap_day(self):
        (actual_min, actual_max) = sut.get_interval(self.options)
        self.assertEqual(actual_min, '2017-02-28')
        self.assertEqual(actual_max, '2020-02-29')

    @freeze_time("2020-02-20")
    def test_regular_february(self):
        (actual_min, actual_max) = sut.get_interval(self.options)
        self.assertEqual(actual_min, '2017-02-20')
        self.assertEqual(actual_max, '2020-02-20')

    @freeze_time("2020-03-29")
    def test_regular_29(self):
        (actual_min, actual_max) = sut.get_interval(self.options)
        self.assertEqual(actual_min, '2017-03-29')
        self.assertEqual(actual_max, '2020-03-29')


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

    @freeze_time("2020-01-01")
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

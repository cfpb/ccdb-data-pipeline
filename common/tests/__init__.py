import sys
from contextlib import contextmanager


def build_argv(optional=[], positional=[]):
    import itertools

    return [x for x in itertools.chain(['prog'], optional, positional)]


@contextmanager
def captured_output(argv):
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

    try:
        from unittest.mock import patch
    except ImportError:
        from mock import patch

    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        with patch.object(sys, 'argv', argv):
            yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def make_configargs(options):
    from argparse import Namespace
    return Namespace(**options)


def noop_coroutine(options, outfile):
    from builtins import range
    for i in range(10000):
        yield i


def validate_files(actual_file, expected_file):
    import io

    with io.open(actual_file, 'r', encoding='utf-8') as f:
        actuals = [line for line in f]

    with io.open(expected_file, 'r', encoding='utf-8') as f:
        expecteds = [line for line in f]

    assert len(actuals) == len(expecteds)

    for i, act in enumerate(actuals):
        assert act == expecteds[i], '[{}]\nexp==>{}<==\nact==>{}<=='.format(
            i, expecteds[i], act)


def validate_json(actual_file, expected_file):
    import io

    with io.open(actual_file, 'r', encoding='utf-8') as f:
        actuals = [line for line in f]

    with io.open(expected_file, 'r', encoding='utf-8') as f:
        expecteds = [line for line in f]

    assert len(actuals) == len(expecteds)

    for i, act in enumerate(actuals):
        # !@#$ Python random dictionary output
        tokens = act.split(',')
        for t in tokens:
            assert t.strip(' {}\n') in expecteds[i], '{} not in {}'.format(
                t, expecteds[i]
            )

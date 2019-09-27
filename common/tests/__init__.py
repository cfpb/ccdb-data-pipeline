import sys
from contextlib import contextmanager


@contextmanager
def captured_output():
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
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


def validate_json(actual_file, expected_file):
    import io

    with io.open(actual_file, 'r', encoding='utf-8') as f:
        actuals = [l for l in f]

    with io.open(expected_file, 'r', encoding='utf-8') as f:
        expecteds = [l for l in f]

    assert len(actuals) == len(expecteds)

    for i, act in enumerate(actuals):
        # !@#$ Python random dictionary output
        tokens = act.split(',')
        for t in tokens:
            assert t.strip(' {}\n') in expecteds[i]

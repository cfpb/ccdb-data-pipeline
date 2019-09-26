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

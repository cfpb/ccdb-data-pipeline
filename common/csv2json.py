from __future__ import print_function
import configargparse
import csv
import json
import io
import os
import sys
from itertools import count

if sys.version < '3':  # pragma: no cover
    _unicode = unicode
else:  # pragma: no cover
    def _unicode(x): return x


# -----------------------------------------------------------------------------
# Unicode is hard
# source https://docs.python.org/2.7/library/csv.html#examples
#   csv.py doesn't do Unicode; encode temporarily as UTF-8:
# -----------------------------------------------------------------------------

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [_unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')


# -----------------------------------------------------------------------------
# Formatter Functions
# -----------------------------------------------------------------------------

def saveNewlineDelimitedJson(options):
    fileName = options.outfile
    with io.open(fileName, 'w', encoding='utf-8', newline='') as f:
        try:
            for i in count():  # pragma: no branch
                row = yield i
                f.write(_unicode(json.dumps(row)))
                f.write(u'\n')
        finally:
            pass


def saveStandardJson(options):
    fileName = options.outfile

    sep = u'\n'
    with io.open(fileName, 'w', encoding='utf-8', newline='') as f:
        f.write(u'[')
        try:
            for i in count():  # pragma: no branch
                row = yield i
                f.write(sep)
                f.write(_unicode(json.dumps(row)))
                sep = u',\n'
        finally:
            f.write(u'\n]')


# -----------------------------------------------------------------------------
# Process
# -----------------------------------------------------------------------------

def run(options):
    formatters = {
        'JSON': saveStandardJson,
        'NDJSON': saveNewlineDelimitedJson
    }
    formatter = formatters[options.jsonFormat](options)
    i = next(formatter)

    with io.open(options.infile, 'r', encoding='utf-8') as f:
        parser = unicode_csv_reader(f)
        columns = next(parser)

        for row in parser:
            obj = dict(zip(columns, row))
            i = formatter.send(obj)

            if (i % 10000) == 0:
                print(' {:,d} rows processed'.format(i))

            if options.limit and i >= options.limit:
                break

    formatter.close()

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def build_arg_parser():
    p = configargparse.ArgParser(prog='csv2json',
                                 description='converts a CSV to JSON',
                                 ignore_unknown_config_file_keys=True)
    p.add('--limit', '-n', dest='limit', type=int, default=0,
          help='Stop at this many records')
    p.add('--json-format', dest='jsonFormat',
          choices=['JSON', 'NDJSON'], default='JSON',
          help='The output format')
    p.add('infile', help="The name of the CSV file")
    p.add('outfile', help="The name of the JSON file to write")
    return p


if __name__ == '__main__':
    p = build_arg_parser()
    cfg = p.parse_args()

    run(cfg)

import csv
import io
import json
from collections import Counter, defaultdict
from datetime import date

import configargparse
from common.constants import THESE_UNITED_STATES

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


# Any more complicated and we should use Arrow
# https://arrow.readthedocs.io/en/latest/
def get_interval(options):
    assert options.interval.upper() == '3Y'

    today = date.today()

    # Dates are hard
    day = 28 if today.day == 29 and today.month == 2 else today.day

    # Compute the interval
    back_then = date(today.year - 3, today.month, day)
    return (
        back_then.strftime('%Y-%m-%d'),
        today.strftime('%Y-%m-%d')
    )


def most_common_value(c):
    # most_common returns [(value1, count)]
    # [0]                 (value1, count1)
    # [0]                 value1
    arr = c.most_common(1)
    return arr[0][0] if len(arr) else ''


# -----------------------------------------------------------------------------
# Tally Classes
# -----------------------------------------------------------------------------

class Tally(defaultdict):
    def __init__(self):
        self.ignored = StateTally('ZZ', 'Not Included', 1)
        super().__init__()

    def __missing__(self, key):
        if key in THESE_UNITED_STATES:
            info = THESE_UNITED_STATES[key]
            return StateTally(key, info['full_name'], info['pop_2017'])
        else:
            print('Skipping "{}"'.format(key))
            return self.ignored

    def __iter__(self):
        for k in THESE_UNITED_STATES:
            yield self[k]

    def process(self, complaint):
        key = complaint['state']
        self[key] += complaint


class StateTally(object):
    def __init__(self, name, full_name, population):
        self.name = name
        self.full_name = full_name
        self.population = population
        self.complaints = 0
        self.issues = Counter()
        self.products = Counter()

    def __iadd__(self, complaint):
        self.complaints += 1
        self.issues.update([complaint['issue']])
        self.products.update([complaint['product']])
        return self

    def __iter__(self):
        yield 'name', self.name
        yield 'fullName', self.full_name
        yield 'value', self.complaints
        yield 'issue', most_common_value(self.issues)
        yield 'product', most_common_value(self.products)
        yield 'perCapita', (self.complaints * 1000) / self.population


# -----------------------------------------------------------------------------
# Process
# -----------------------------------------------------------------------------

def run(options):
    tally = Tally()

    # Determine the range from the interval string
    (min_date, max_date) = get_interval(options)

    with io.open(options.infile, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, dialect=csv.excel)

        # The first line is the columns
        columns = next(reader)

        for i, row in enumerate(reader, 1):  # pragma: no branch
            complaint = dict(zip(columns, row))

            row_date = complaint.get('date_received', '2000-01-01')

            # See if this row falls within the interval
            if row_date >= min_date and row_date <= max_date:
                tally.process(complaint)

            if (i % options.heartbeat) == 0:
                print('{:,d} rows processed'.format(i))

            if options.limit and i >= options.limit:
                break

    # Output the results
    with io.open(options.outfile, 'w', encoding='utf-8') as f:
        results = [dict(x) for x in tally]
        json.dump(results, f)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def build_arg_parser():
    p = configargparse.ArgParser(prog='build_hero_map',
                                 description='builds the dataset for hero map',
                                 ignore_unknown_config_file_keys=True)
    p.add('--heartbeat', dest='heartbeat', type=int, default=10000,
          help='Indicate rows are being processed every N records')
    p.add('--interval', choices=['3y'], default='3y',
          help='Indicate the time period to generate')
    p.add('--limit', '-n', dest='limit', type=int, default=0,
          help='Stop at this many records')
    p.add('infile', help="The name of the CSV file")
    p.add('outfile', help="The name of the JSON file to write")
    return p


def main():
    p = build_arg_parser()
    cfg = p.parse_args()

    run(cfg)


if __name__ == '__main__':
    main()

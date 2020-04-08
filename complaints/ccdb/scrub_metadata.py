import errno
import io
import json
import sys

import configargparse

VALID_ATTR = ['metadata_timestamp', 'qas_timestamp', 'total_count']

# -----------------------------------------------------------------------------
# Process
# -----------------------------------------------------------------------------


def load_metadata(filename):
    with io.open(filename, 'r', encoding='utf-8') as f:
        try:
            jo = json.load(f)
        except Exception:
            print("'{0}' is not a valid JSON document.".format(filename),
                  file=sys.stderr)
            sys.exit(errno.ENOENT)
    return jo


def save_metadata(metadata, filename):
    try:
        with io.open(filename, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, sort_keys=True)
    except Exception:
        print("Unable to write '{0}'".format(filename), file=sys.stderr)
        sys.exit(errno.EIO)


def scrub(options):
    internal = load_metadata(options.infile)
    external = {k: internal[k] for k in VALID_ATTR if k in internal}

    if len(external) != len(VALID_ATTR):
        print("'{0}' is missing one or more of {1}".format(
            options.infile, ', '.join(VALID_ATTR)), file=sys.stderr)
        sys.exit(errno.EPERM)

    save_metadata(external, options.outfile)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def build_arg_parser():
    p = configargparse.ArgParser(
        prog='scrub_metadata',
        description='preserves a specific list of attributes'
    )
    p.add('infile', help="The name of the internal metadata file")
    p.add('outfile', help="The name of the public metadata file")
    return p


def main():
    p = build_arg_parser()
    options = p.parse_args()

    scrub(options)


if __name__ == '__main__':
    main()

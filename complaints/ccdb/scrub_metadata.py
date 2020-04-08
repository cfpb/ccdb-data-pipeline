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
            print("'%s' is not a valid JSON document.".format(filename),
                  file=sys.stderr)
            sys.exit(errno.ENOENT)
    return jo


def scrub(options):
    internal = load_metadata(options.infile)
    external = {k: internal[k] for k in VALID_ATTR}

    if len(external) != len(VALID_ATTR):
        print("'%s' is missing one or more of %s".format(
            options.infile, ', '.join(VALID_ATTR)), file=sys.stderr)
        sys.exit(errno.EPERM)

    with io.open(options.outfile, 'w', encoding='utf-8') as f:
        try:
            json.dump(external, f, indent=2, sort_keys=True)
        except Exception:
            print("Unable to write '%s'".format(options.outfile),
                  file=sys.stderr)
            sys.exit(errno.EIO)

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

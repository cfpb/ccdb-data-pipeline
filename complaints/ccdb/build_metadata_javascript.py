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


def save_javascript(metadata, filename):
    try:
        with io.open(filename, 'w', encoding='utf-8') as f:
            f.write('var complaint_public_metadata = ')
            json.dump(metadata, f, indent=2, sort_keys=True)
    except Exception:
        print("Unable to write '{0}'".format(filename), file=sys.stderr)
        sys.exit(errno.EIO)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def build_arg_parser():
    p = configargparse.ArgParser(
        prog='build_metadata_javascript',
        description='makes metadata that can be statically loaded in a JS app'
    )
    p.add('infile', help="The name of the public metadata file")
    p.add('outfile', help="The name of the Javascript file")
    return p


def main():
    p = build_arg_parser()
    options = p.parse_args()

    save_javascript(load_metadata(options.infile), options.outfile)


if __name__ == '__main__':
    main()

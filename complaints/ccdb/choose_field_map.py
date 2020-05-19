import errno
import io
import os
import shutil
import sys

import configargparse

INTAKE_V1 = "date_received,product,sub_product,issue,sub_issue," \
            "consumer_narrative,company_public_response,company,state," \
            "zip_code,tag,consent_status,submitted_via,date_sent_to_company," \
            "company_response_to_consumer,timely_response,consumer_disputed," \
            "public_id"
PUBLIC_V1 = "Date received,Product,Sub-product,Issue,Sub-issue," \
            "Consumer complaint narrative,Company public response,Company," \
            "State,ZIP code,Tags,Consumer consent provided?,Submitted via," \
            "Date sent to company,Company response to consumer," \
            "Timely response?,Consumer disputed?,Complaint ID"

INTAKE_V2 = INTAKE_V1 + ",event_tag"
PUBLIC_V2 = PUBLIC_V1 + ",Event tag"

# -----------------------------------------------------------------------------
# Process
# -----------------------------------------------------------------------------


def run(options):
    # Get the number of columns from the intake file
    with io.open(options.infile, 'r', encoding='utf-8') as f:
        src_columns = next(f).strip()

    # Figure out which file map to use
    version = None
    if src_columns == INTAKE_V1 or src_columns == PUBLIC_V1:
        version = 'v1'
    elif src_columns == INTAKE_V2 or src_columns == PUBLIC_V2:
        version = 'v2'

    if version is None:
        sys.stderr.write('\nUnknown field set\n\t"{}"\n\n'.format(src_columns))
        sys.stderr.flush()
        sys.exit(errno.ENOENT)

    # Make the full filename
    src_fields = '{}-{}.txt'.format(version, options.target_format.lower())
    thisScriptDir = os.path.dirname(__file__)
    filename = os.path.join(thisScriptDir, 'fields-s3', src_fields)

    # Copy
    print('Using "{}" for field mapping'.format(src_fields))
    shutil.copy(filename, options.outfile)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def build_arg_parser():
    p = configargparse.ArgParser(prog='choose_field_map',
                                 description='pairs a field map with a CSV',
                                 ignore_unknown_config_file_keys=True)
    p.add('--target-format', dest='target_format',
          choices=['JSON', 'CSV'], default='JSON',
          help='The format of the output to target')
    p.add('infile', help="The name of the intake file")
    p.add('outfile', help="The name of the file to write")
    return p


def main():
    p = build_arg_parser()
    cfg = p.parse_args()

    run(cfg)


if __name__ == '__main__':
    main()

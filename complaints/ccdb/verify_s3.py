from __future__ import print_function

import os
import sys
from zipfile import ZipFile

import boto3
import configargparse

# -----------------------------------------------------------------------------
# Process
# -----------------------------------------------------------------------------


class ProgressPercentage(object):
    def __init__(self, options):
        self.options = options
        self.seen_so_far = 0

    def __call__(self, bytes_amount):
        self.seen_so_far += bytes_amount
        sys.stdout.write(
            "\r{}  {:,d} bytes".format(self.options.infile, self.seen_so_far)
        )
        sys.stdout.flush()


def verify(options):
    # Setup
    temp_json_file_name = "todays_json_export.json"
    size_file_path = "complaints/ccdb/json_prev_size.txt"

    path, base_filename = os.path.split(options.json_file)
    key = options.folder + '/' + base_filename + '.zip'

    # Execute
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(options.bucket)
    bucket.download_file(key,
                         "{}.zip".format(temp_json_file_name),
                         Callback=ProgressPercentage(options))

    # AZ - Use the following to unzip the files if desired
    # with ZipFile("{}.zip".format(temp_json_file_name), 'r') as zip_ref:
    #     zip_ref.extractall("")
    # new_size = os.path.getsize(base_filename)

    try:
        with open(size_file_path, 'r') as f:
            prev_size = int(f.read())
    except Exception:
        prev_size = 0

    new_size = os.path.getsize("{}.zip".format(temp_json_file_name))

    if new_size < prev_size:
        print("\n\nPROBLEM!!!\nNew Size: {}\nPrev Size: {}\n\n".format(
              new_size, prev_size))
    else:
        print("\n\nNO PROBLEM!\nNew Size: {}\nPrev Size: {}\n\n".format(
              new_size, prev_size))
        with open(size_file_path, 'w+') as f:
            f.write(str(new_size))

    # Clean up
    os.remove("{}.zip".format(temp_json_file_name))
    # os.remove(base_filename)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def build_arg_parser():
    p = configargparse.ArgParser(
        prog='verify_s3',
        description='ensure the uploaded s3 files are growing',
        ignore_unknown_config_file_keys=True,
        default_config_files=['./config.ini'],
        args_for_setting_config_path=['-c', '--config'],
        args_for_writing_out_config_file=['--save-config']
    )
    p.add('--dump-config', action='store_true', dest='dump_config',
          help='dump config vars and their source')
    group = p.add_argument_group('S3')
    group.add('--s3-bucket', '-b', dest='bucket',
              required=True, env_var='OUTPUT_S3_BUCKET',
              help='The S3 bucket that will contain the data')
    group.add('--s3-folder', dest='folder',
              required=True, env_var='OUTPUT_S3_FOLDER',
              help='The S3 path to use')
    group = p.add_argument_group('Files')
    group.add(dest='json_file',
              help="Name of the json data file")
    group.add(dest='infile',
              help="The local name of the file to write")
    return p


def main():
    p = build_arg_parser()
    cfg = p.parse_args()

    if cfg.dump_config:
        print(p.format_values())

    verify(cfg)


if __name__ == '__main__':
    main()

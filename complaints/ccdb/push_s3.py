import os
import sys
from zipfile import ZIP_DEFLATED, ZipFile

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


def upload_zip(options):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(options.bucket)

    path, filename = os.path.split(options.infile)
    key = options.folder + '/' + filename + '.zip'
    zip_file_name = '{}.zip'.format(filename)

    with ZipFile(zip_file_name, 'w', ZIP_DEFLATED) as zip:
        # AZ - The following is necessary to ensure the file ends up in the
        # root of the zip directory
        if '.json' in filename:
            pwd = os.getcwd()
            os.chdir(path)
            zip.write(filename)
            os.chdir(pwd)
        else:
            zip.write(options.infile, filename)

    bucket.upload_file(
        zip_file_name, key, Callback=ProgressPercentage(options)
    )

    # Clear the buffer
    sys.stdout.write("\n")
    sys.stdout.flush()

    # Delete the local zip file
    os.remove(zip_file_name)


def upload_raw(options):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(options.bucket)

    _, filename = os.path.split(options.infile)
    key = options.folder + '/' + filename

    bucket.upload_file(
        options.infile, key, Callback=ProgressPercentage(options)
    )

    # Clear the buffer
    sys.stdout.write("\n")
    sys.stdout.flush()


def upload(options):
    if options.no_zip:
        upload_raw(options)
    else:
        upload_zip(options)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def build_arg_parser():
    p = configargparse.ArgParser(
        prog='acquire',
        description='retrieves the latest S3 file',
        ignore_unknown_config_file_keys=True,
        default_config_files=['./config.ini'],
        args_for_setting_config_path=['-c', '--config'],
        args_for_writing_out_config_file=['--save-config']
    )
    p.add('--dump-config', action='store_true', dest='dump_config',
          help='dump config vars and their source')
    p.add('--no-zip', action='store_true', dest='no_zip',
          help='do not zip contents before uploading')
    group = p.add_argument_group('S3')
    group.add('--s3-bucket', '-b', dest='bucket',
              required=True, env_var='OUTPUT_S3_BUCKET',
              help='The S3 bucket that will contain the data')
    group.add('--s3-folder', dest='folder',
              required=True, env_var='OUTPUT_S3_FOLDER',
              help='The S3 path to use')
    group = p.add_argument_group('Files')
    group.add(dest='infile',
              help="The local name of the file to write")
    return p


def main():
    p = build_arg_parser()
    cfg = p.parse_args()

    if cfg.dump_config:
        print(p.format_values())

    upload(cfg)


if __name__ == '__main__':
    main()

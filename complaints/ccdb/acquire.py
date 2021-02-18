import sys

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
            "\r{}  {:,d} bytes".format(self.options.outfile, self.seen_so_far)
        )
        sys.stdout.flush()


def check_latest(options):
    import os

    import pytz

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(options.bucket)
    dataset = bucket.Object(options.key)

    utc_dt = dataset.last_modified
    local_dt = utc_dt.astimezone(pytz.timezone(options.timezone))
    timestamp = int(local_dt.timestamp())

    if not os.path.exists(options.outfile):
        open(options.outfile, 'a').close()

    # Get the current timestamp
    stat = os.stat(options.outfile)

    # Set the modification time of the file to be the same as the dataset
    if stat.st_mtime != timestamp:
        os.utime(options.outfile, (timestamp, timestamp))
    else:
        print('\nNo new data set since', local_dt.strftime(
            '%I:%S %p %A, %B %d, %Y'
        ))


def download(options):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(options.bucket)

    bucket.download_file(options.key, options.outfile,
                         Callback=ProgressPercentage(options))

    # Clear the buffer
    sys.stdout.write("\n")
    sys.stdout.flush()


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
    p.add('--check-latest', '-t', action='store_true',
          dest='get_latest',
          help='check the timestamp of the most recent dataset')
    p.add('--timezone', dest='timezone',
          default='US/Eastern',
          help='The local timezone specified in Olsen format')
    group = p.add_argument_group('S3')
    group.add('--s3-bucket', '-b', dest='bucket',
              required=True, env_var='INPUT_S3_BUCKET',
              help='The S3 bucket that contains the data')
    group.add('--s3-key', '-k', dest='key',
              required=True, env_var='INPUT_S3_KEY',
              help='The S3 path to the data')
    group = p.add_argument_group('Files')
    group.add('--outfile', '-o',
              dest='outfile', required=True,
              help="The local name of the file to write")
    return p


def main():
    p = build_arg_parser()
    cfg = p.parse_args()

    if cfg.dump_config:
        print(p.format_values())

    if cfg.get_latest:
        check_latest(cfg)
    else:
        download(cfg)


if __name__ == '__main__':
    main()

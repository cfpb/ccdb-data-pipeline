import csv
import os
from datetime import datetime
from zipfile import ZIP_DEFLATED, ZipFile

import boto3


def download_file(bucket, key, file):
    s3 = boto3.resource("s3")
    bkt = s3.Bucket(bucket)
    bkt.download_file(key, file)


def append_to_zip(zip_name, datafile):
    filename = zip_name[:-4]

    with ZipFile(zip_name, "r") as zip_ref:
        zip_ref.extractall(".")

    write_and_zip(datafile, filename, "a")


def upload_file(bucket, key, file):
    s3 = boto3.resource("s3")
    bkt = s3.Bucket(bucket)
    bkt.upload_file(file, key)


def update_zipped_archive(bucket, key, new_data):
    _, zip_name = os.path.split(key)
    download_file(bucket, key, zip_name)
    append_to_zip(zip_name, new_data)
    upload_file(bucket, key, zip_name)


def create_zipped_archive(bucket, key, new_data):
    _, zip_name = os.path.split(key)
    filename = zip_name[:-4]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    header_file = os.path.join(base_dir, "complaints/ccdb/fields-s3/v1-csv.txt")
    with open(header_file, "r") as f:
        public_header = f.read().splitlines()
        write_and_zip(new_data, filename, header=public_header)
    upload_file(bucket, key, zip_name)


def write_and_zip(in_file, out_file, mode="w", header=None):
    with open(in_file, "r", newline="") as infile:
        with open(out_file, mode, newline="") as outfile:
            reader = csv.reader(infile)
            # Remove header from infile
            next(reader)

            writer = csv.writer(outfile, lineterminator="\n")

            if header:
                writer.writerow(header)
            for row in reader:
                row[0] = ymd(row[0])
                if row[13]:
                    row[13] = ymd(row[13])
                writer.writerow(row)

    with ZipFile(f"{out_file}.zip", "w", ZIP_DEFLATED) as zip:
        zip.write(out_file)


def ymd(iso):
    return datetime.fromisoformat(iso).strftime("%Y-%m-%d")

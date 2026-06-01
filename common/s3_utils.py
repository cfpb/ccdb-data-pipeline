import csv
import os
from datetime import datetime
from zipfile import ZIP_DEFLATED, ZipFile

import boto3


def download_file(bucket, prefix, file):
    s3 = boto3.resource("s3")
    bkt = s3.Bucket(bucket)
    bkt.download_file(f"{prefix}{file}", file)


def append_to_zip(zip_name, datafile):
    filename = zip_name[:-4]

    with ZipFile(zip_name, "r") as zip_ref:
        zip_ref.extractall(".")

    new_ids = {}

    with open("temp_file", "w", newline="") as tempfile:
        with open(filename, "r", newline="") as original_file:
            orig_reader = csv.reader(original_file)
            tempfile.writerow(next(orig_reader))

            with open(datafile, "r", newline="") as file_to_append:
                append_reader = csv.reader(file_to_append)
                next(append_reader)
                for row in append_reader:
                    new_ids[row[15]] = 1
                    tempfile.writerow(row)

            for row in orig_reader:
                if new_ids.get(row[15]):
                    continue
                tempfile.writerow(row)

    os.replace("temp_file", filename)

    make_zip(filename)


def upload_file(bucket, prefix, file):
    s3 = boto3.resource("s3")
    bkt = s3.Bucket(bucket)
    bkt.upload_file(file, f"{prefix}{file}")


def update_zipped_archives(bucket, prefix, basename, new_data):
    csv_filename = f"{basename}.csv"
    zipped_csv = f"{csv_filename}.zip"

    download_file(bucket, prefix, zipped_csv)
    append_to_zip(zipped_csv, new_data)
    upload_file(bucket, prefix, zipped_csv)


def create_zipped_archives(bucket, prefix, basename, new_data):
    csv_filename = f"{basename}.csv"
    zipped_csv = f"{csv_filename}.zip"

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    header_file = os.path.join(base_dir, "complaints/ccdb/fields-s3/v1-csv.txt")
    with open(header_file, "r") as f:
        public_header = f.read().splitlines()
        write_csv(new_data, csv_filename, header=public_header)
    make_zip(csv_filename, zipped_csv)
    upload_file(bucket, prefix, zipped_csv)


def write_csv(in_file, out_file, mode="w", header=None):
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
                if row[12]:
                    row[12] = ymd(row[12])
                writer.writerow(row)


def make_zip(file, zipped):
    with ZipFile(zipped, "w", ZIP_DEFLATED) as zip:
        zip.write(file)


def ymd(iso):
    return datetime.fromisoformat(iso).strftime("%Y-%m-%d")

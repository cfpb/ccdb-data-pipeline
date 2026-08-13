import csv
import os
from datetime import datetime
from zipfile import ZIP_DEFLATED, ZipFile

import boto3

from common.log import setup_logging

logger = setup_logging("s3_utils")


def download_file(bucket, prefix, file):
    logger.info(f"Downloading file: {file}")
    s3 = boto3.resource("s3")
    bkt = s3.Bucket(bucket)
    bkt.download_file(f"{prefix}{file}", file)


def append_to_zip(zip_name, datafile):
    logger.info("Appending to zip")
    csv_filename = zip_name[:-4]

    with ZipFile(zip_name, "r") as zip_ref:
        zip_ref.extractall(".")

    new_ids = {}

    with open("temp_file", "w", newline="") as tempfile:
        with open(csv_filename, "r", newline="") as original_file:
            orig_reader = csv.reader(original_file)
            temp_writer = csv.writer(tempfile, lineterminator="\n")
            temp_writer.writerow(next(orig_reader))

            with open(datafile, "r", newline="") as file_to_append:
                append_reader = csv.reader(file_to_append)
                next(append_reader)
                for row in append_reader:
                    # If ineligible, skip both here and in orig file
                    if row[16] != "true":
                        if row[15]:
                            new_ids[row[15]] = 1
                        continue
                    new_ids[row[15]] = 1

                    temp_writer.writerow(process_row(row))

            for row in orig_reader:
                if new_ids.get(row[15]):
                    continue
                temp_writer.writerow(row)

    os.replace("temp_file", csv_filename)

    make_zip(csv_filename, f"{csv_filename}.zip")


def upload_file(bucket, prefix, file):
    logger.info(f"Uploading file: {file}")
    s3 = boto3.resource("s3")
    bkt = s3.Bucket(bucket)
    bkt.upload_file(file, f"{prefix}{file}")


def update_zipped_archive(bucket, prefix, basename, new_data):
    logger.info("Updating zipped archives")

    csv_filename = f"{basename}.csv"
    zipped_csv = f"{csv_filename}.zip"

    download_file(bucket, prefix, zipped_csv)
    append_to_zip(zipped_csv, new_data)
    upload_file(bucket, prefix, zipped_csv)


def create_zipped_archive(bucket, prefix, basename, new_data):
    logger.info("Creating zipped archives")

    csv_filename = f"{basename}.csv"
    zipped_csv = f"{csv_filename}.zip"

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    header_file = os.path.join(base_dir, "complaints/ccdb/fields/csv.txt")
    with open(header_file, "r") as f:
        public_header = f.read().splitlines()
        write_csv(new_data, csv_filename, public_header)

    make_zip(csv_filename, zipped_csv)
    upload_file(bucket, prefix, zipped_csv)


def write_csv(in_file, out_file, header):
    logger.info(f"Writing to csv: {out_file}")

    with open(in_file, "r", newline="") as infile:
        with open(out_file, "w", newline="") as outfile:
            reader = csv.reader(infile)
            # Remove header from infile
            next(reader)

            writer = csv.writer(outfile, lineterminator="\n")
            writer.writerow(header)

            for row in reader:
                writer.writerow(process_row(row))


def process_row(row):
    # Simplify dates
    row[0] = ymd(row[0])
    if row[12]:
        row[12] = ymd(row[12])

    # Remove newlines from narrative
    row[5] = " ".join(row[5].split())

    # Trim 'eligible' field
    return row[:16]


def make_zip(file, zipped):
    with ZipFile(zipped, "w", ZIP_DEFLATED) as zip:
        zip.write(file)


def ymd(iso):
    return datetime.fromisoformat(iso).strftime("%Y-%m-%d")

import csv
import os
import subprocess
from datetime import datetime
from zipfile import ZIP_DEFLATED, ZipFile

import boto3


def download_file(bucket, prefix, file):
    s3 = boto3.resource("s3")
    bkt = s3.Bucket(bucket)
    bkt.download_file(f"{prefix}{file}", file)


def append_to_zips(zip_name, datafile):
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
                    new_ids[row[15]] = 1
                    temp_writer.writerow(row)

            for row in orig_reader:
                if new_ids.get(row[15]):
                    continue
                temp_writer.writerow(row)

    os.replace("temp_file", csv_filename)

    json_filename = make_json(csv_filename)

    make_zip(csv_filename, f"{csv_filename}.zip")
    make_zip(json_filename, f"{json_filename}.zip")


def make_json(csv_filename):
    json_filename = f"{csv_filename[:-4]}.json"
    subprocess.run(
        [
            "python",
            "common/csv2json.py",
            "--json-format",
            "JSON",
            "--fields",
            "complaints/ccdb/fields-s3/v1-json.txt",
            csv_filename,
            json_filename,
        ],
        check=True,
    )
    return json_filename


def upload_file(bucket, prefix, file):
    s3 = boto3.resource("s3")
    bkt = s3.Bucket(bucket)
    bkt.upload_file(file, f"{prefix}{file}")


def update_zipped_archives(bucket, prefix, basename, new_data):
    csv_filename = f"{basename}.csv"
    zipped_csv = f"{csv_filename}.zip"
    zipped_json = f"{basename}.json.zip"

    download_file(bucket, prefix, zipped_csv)
    append_to_zips(zipped_csv, new_data)
    upload_file(bucket, prefix, zipped_csv)
    upload_file(bucket, prefix, zipped_json)


def create_zipped_archives(bucket, prefix, basename, new_data):
    csv_filename = f"{basename}.csv"
    zipped_csv = f"{csv_filename}.zip"

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    header_file = os.path.join(base_dir, "complaints/ccdb/fields-s3/v1-csv.txt")
    with open(header_file, "r") as f:
        public_header = f.read().splitlines()
        write_csv(new_data, csv_filename, header=public_header)

    json_filename = make_json(csv_filename)
    zipped_json = f"{json_filename}.zip"
    make_zip(csv_filename, zipped_csv)
    make_zip(json_filename, zipped_json)
    upload_file(bucket, prefix, zipped_csv)
    upload_file(bucket, prefix, zipped_json)


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

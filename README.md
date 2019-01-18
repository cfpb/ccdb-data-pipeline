# CCDB Data Pipeline

A lightweight ETL data pipeline intended to support the operations of the Consumer Complaint Search application.

**Description**: This purpose of this code is to provide data for Consumer Complaint Search. This pipeline downloads scrubbed consumer complaint data and indexes that data in Elasticsearch for the Complaint Search application to display and analyze.

**Status**:  In Production

## Dependencies

This pipeline is intended to index data in Elasticsearch and is dependent on having an Elasticsearch instance to interface with.

## Installation

Detailed instructions on how to install, configure, and get the project running are in the [INSTALL](INSTALL.md) document.

## Usage

1. `source ./activate-virtualenv.sh`
1. Set environment variables
    1. `export AWS_ACCESS_KEY_ID=<svc_account_access_key>`
    1. `export AWS_SECRET_ACCESS_KEY=<svc_account_secret_access_key>`
    1. `export CCDB_S3_BUCKET=<bucket-name>`
    1. `export CCDB_S3_KEY=<path-to-csv>`
    1. `export ES_USERNAME=<foo>`
    1. `export ES_PASSWORD=<bar>`
    1. `export ENV=[ENVIRONMENT]`
        1. where ENVIRONMENT=`dev`, `staging`, `prod`
1. `make`

## Getting help

Instruct users how to get help with this software; this might include links to an issue tracker, wiki, mailing list, etc.


## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)

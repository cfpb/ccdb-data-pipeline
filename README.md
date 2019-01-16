# CCDB Data Pipeline

A lightweight ETL data pipeline intended to support the operations of the Consumer Complaint Search application.

**Description**: This purpose of this code is to provide data for Consumer Complaint Search. This pipeline downloads scrubbed consumer complaint data and indexes that data in Elasticsearch for the Complaint Search application to display and analyze.

**Status**:  In Production

## Dependencies

This pipeline is intended to index data in Elasticsearch and is dependent on having an Elasticsearch instance to interface with.

## Installation

Detailed instructions on how to install, configure, and get the project running are in the [INSTALL](INSTALL.md) document.

## Usage

usage: run_pipeline [-h] -c MY_CONFIG --es-host ES_HOST --es-port ES_PORT
                    [--es-username ES_USERNAME] [--es-password ES_PASSWORD]
                    --index-name INDEX_NAME

Arguments:
* -h, --help
    * show this help message and exit
* -c MY_CONFIG, --my-config MY_CONFIG
    * config file path
* --es-host ES_HOST, -o ES_HOST
    * Elasticsearch host (**Required Parameter**)
* --es-port ES_PORT, -p ES_PORT
    * Elasticsearch port (**Required Parameter**)
* --es-username ES_USERNAME, -u ES_USERNAME
    * Elasticsearch username
* --es-password ES_PASSWORD, -a ES_PASSWORD
    * Elasticsearch password
* --index-name INDEX_NAME, -i INDEX_NAME
    * Elasticsearch index name (**Required Parameter**)

Though the arguments ES_HOST, ES_PORT and INDEX_NAME are required, you may choose to combine those values into a config file and provide that as an argument instead. For config file syntax, see [here](https://goo.gl/R74nmi). If an arg is specified in more than one place, then commandline values override environment variables which override config file values which override defaults.

## Getting help

Instruct users how to get help with this software; this might include links to an issue tracker, wiki, mailing list, etc.


## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)

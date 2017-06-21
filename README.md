# CCDB Data Pipeline

**Description**: This purpose of this code is to provide data for Consumer Complaint Search. This pipeline downloads scrubbed consumer complaint data and indexes that data in Elasticsearch for the Complaint Search to use.

Other things to include:

  - **Technology stack**: 
  - **Status**:  Alpha

## Dependencies

This pipeline is intended to index data in Elasticsearch, and therefore is dependent on having an Elasticsearch instance to interface with.

## Usage

usage: run_pipeline [-h] -c MY_CONFIG --es-host ES_HOST --es-port ES_PORT
                    --es-username ES_USERNAME --es-password ES_PASSWORD
                    --index-name INDEX_NAME

download complaints and index in Elasticsearch Args that start with '--' (eg.
--es-host) can also be set in a config file (specified via -c). Config file
syntax allows: key=value, flag=true, stuff=[a,b,c] (for details, see syntax at
https://goo.gl/R74nmi). If an arg is specified in more than one place, then
commandline values override environment variables which override config file
values which override defaults.

Arguments:
* -h, --help
    * show this help message and exit
* -c MY_CONFIG, --my-config MY_CONFIG
    * config file path
* --es-host ES_HOST, -o ES_HOST
    * Elasticsearch host [env var: ES_HOST]
    * **Required Parameter**
* --es-port ES_PORT, -p ES_PORT
    * Elasticsearch port [env var: ES_PORT]
    * **Required Parameter**
* --es-username ES_USERNAME, -u ES_USERNAME
    * Elasticsearch username [env var: ES_USERNAME]
* --es-password ES_PASSWORD, -a ES_PASSWORD
    * Elasticsearch password [env var: ES_PASSWORD]
* --index-name INDEX_NAME, -i INDEX_NAME
    * Elasticsearch index name
    * **Required Parameter**

Though the arguments ES_HOST, ES_PORT and INDEX_NAME are required, you may choose to combine those values into a config file and provide that as an argument instead.

## Getting help

Instruct users how to get help with this software; this might include links to an issue tracker, wiki, mailing list, etc.

----

## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)

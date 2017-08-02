# Installation instructions

## Installing

```bash
# Clone the project from github
git clone https://github.com/cfpb/ccdb-data-pipeline.git
cd ccdb-data-pipeline
```

## Configuration
Either add the necessary configuration information for Elasticsearch. This can be done by modifying the `config_sample.ini` file, creating your own configuration file, or by passing the arguments directly to the script via command line. See the 

The Elasticsearch Host, Port, and desired Index Name are required parameters for the pipeline script. Parameters have been provided to account for optional Elasticsearch credentials (username and password) if desired.

## Run the pipeline script

To provide parameters via a configuration file, use this syntax:

`python run_pipeline.py -c [configuration file]`

Example:
```bash
# Config file example
python run_pipeline.py -c config_sample.ini
```

To provide parameters via script arguments, use this syntax:

`python run_pipeline.pt -o [Elasticsearch Host] -p [Elasticsearch Port] -i [Elasticsearch Index Name]`

Example
```bash
# Script parameters example
python run_pipeline.py -o localhost -p 9200 -i my_index
```
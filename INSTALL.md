# Installation instructions

## Installing

```bash
# Clone the project from github
git clone https://github.com/cfpb/ccdb-data-pipeline.git
cd ccdb-data-pipeline
source ./activate-virtualenv.sh
pip install -r requirements.txt
```

## Configuration
Add the necessary configuration information for Elasticsearch. This can be done by copying and modifying the `config_sample.ini` file, creating your own configuration file, or by passing the arguments directly to the script via command line.

For config file syntax, see [here](https://goo.gl/R74nmi).

##### Evaluation Order

The configuration is loaded from the following sources.  If the value appears in more than one location, the earliest found version wins

1. Command Line
1. Environment Variable
1. Config File Entry
1. default value

# Local installation

### The CCDB repos

The CCDB project is broken into three repos, which isolates code for indexing (this repository), searching ([ccdb5-api](https://github.com/cfpb/ccdb5-api)), and user interface ([ccdb5-ui](https://github.com/cfpb/ccdb5-ui)). The public data are produced in a pipeline that begins with original complaints stored in an internal database and ends with a public CSV file, which is scrubbed of PII and updated on S3 every morning. The CSV is then indexed in our production Elasticsearch service.

The separation of concerns allows us to run the complaint pipeline from source to Elasticsearch without involving consumerfinance.gov code. But the separation makes it tricky to get a local development environment running with indexed data along with development versions of code from the various repos.

### An indexing task

One hurdle is how to get current complaint data indexed locally in Elasticsearch and how to explore the resulting index.

Docker is a great choice for this, because it's easy to get Elasticsearch and its useful Kibana console running locally in tandem. Until we get Kibana approved for our production Elasticsearch services, this makes local Kibana access even more valuable.

This leaves a decision about how to run the rest of the project's code. Running a hybrid setup has advantages if you work mainly in Python and use its debugging features. If you mostly work on front-end code, a Docker-only rig may be a good choice.

### Option 1: A hybrid local setup for Python

We routinely run consumerfinance.gov [in Docker](https://cfpb.github.io/consumerfinance.gov/running-docker/), but trying to run the full cfgov + CCDB stack in Docker can be time-consuming and tricky, in part because the indexing is not handled in the cfgov environment. That makes it easy to get mismatched index names and environment variables and burn time rebuilding Docker containers. 

One useful option is to let Docker serve Elasticsearch, Kibana and Postgres, and run Python code in a local environment. You can do this by starting the full suite of consumerfinance.gov Docker containers with `docker-compose up`, and then run `docker-compose stop python`. That way you can locally run the Django server (with `./runserver.sh`), adjust env variables on the fly without rebuilding containers, and set pdb traces without attaching to a container. Elasticsearch will be available at localhost:9200 and Kibana at <http://localhost:5601/app/dev_tools#/console>, and Postgres will work the same as a local instance, including allowing you to load production content data (using the refresh-data.sh script) without jumping into a container.

This setup assumes you have a working local consumerfinance.gov environment set up. Follow steps in the public cfgov setup docs for [standalone](https://cfpb.github.io/consumerfinance.gov/installation/#stand-alone-installation), but skipping Postgres and Elasticsearch setups, and then follow [docker](https://cfpb.github.io/consumerfinance.gov/installation/#stand-alone-installation) installation instructions.

To work on front-end and back-end code, you can clone branches of ccdb5-api and ccdb5-ui locally and install them into your cfgov virtual env by running `pip install -e .` (note the dot) from each repo's root.

In the environment where cfgov is running, make sure the following env vars are available. They are probably commented out and incomplete in your .env file, so uncomment and edit them to match, and then use `source .env` to load them. This makes sure the CCDB search API is using the same index that the Elasticsearch pipeline will build:

```bash
export COMPLAINT_ES_INDEX=complaint-public-dev
```

### Option 2: A Docker-only setup

If you're not concerned with Python-specific tools like pdb, you can run the whole setup in Docker and skip local virtualenv setup. Just make sure you uncomment and edit these lines in your local .env file before running `docker-compose up`:

```bash
export COMPLAINT_ES_INDEX=complaint-public-dev
export ES_HOST=elasticsearch
```

When running everything in Docker, you can clone branches of ccdb5-ui and ccdb5-api into the develop-apps folder and work on them there. This location will expose them to the Python Docker container.

### Building the complaint index

Once you have Elasticsearch running in Docker and available at localhost:9200, via either option 1 or 2, you can get your index populated with the latest complaint data.

First create and activate a Python3 virtualenv for the data pipeline, then clone and set up the project.

```bash
pyenv virtualenv 3.6.9 ccdb-data-pipeline && pyenv activate ccdb-data-pipeline
git clone https://github.com/cfpb/ccdb-data-pipeline.git
cd ccdb-data-pipeline
cp config_sample.ini config.ini
pip install -r requirements.txt
```

Copy the sample env file and source it:
```bash
cp .env_example .env
source .env
```

That should set these required env variables for you:  
```bash
export ES_USERNAME=elasticsearch
export ES_PASSWORD=""
export ENV=dev
```

Optional:

To reduce your load time, set the MAX_RECORDS env variable to any number to load a subset of records of available complaints.
```bash
export MAX_RECORDS=10000
```


Confirm that Elasticsearch is running at localhost:9200

```bash
curl localhost:9200
```

That should return something like this:

```bash
{
  "name" : "6a91ecd93c82",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "XqMcQxTzTX6IQ6qqJ1-zAg",
  "version" : {
    "number" : "7.10.1",
    "build_flavor" : "oss",
    "build_type" : "tar",
    "build_hash" : "1c34507e66d7db1211f66f3513706fdf548736aa",
    "build_date" : "2020-12-05T01:00:33.671820Z",
    "build_snapshot" : false,
    "lucene_version" : "8.7.0",
    "minimum_wire_compatibility_version" : "6.8.0",
    "minimum_index_compatibility_version" : "6.0.0-beta1"
  },
  "tagline" : "You Know, for Search"
}
```


Now you can run the ccdb-data-pipeline to index public CCDB complaint data.

```bash
make from_public
```

The pipeline will download two public data files – a 2-million-row CSV of complaints and a json file of metadata – prep them for indexing, and then index them in Elasticsearch. This will take a while.

After the index builds, you can confirm it in your local [Kibana console](<http://localhost:5601/app/dev_tools#/console>) by running this command:

```bash
GET /_cat/indices
```

Kibana has some nice autocompletion helpers for testing queries and for other uses of the Elasticsearch API.  
See the Kibana [console docs](https://www.elastic.co/guide/en/kibana/current/console-kibana.html) to dig deeper.

You should now have the complaint search running with the latest data at <http://localhost:8000/data-research/consumer-complaints/search/>.

## Working on the production pipeline

To test and develop the prod pipeline, which runs in Jenkins to populate the production Elasticsearch index and post files to S3, you'll need a few more values in your env:

```bash
export AWS_ACCESS_KEY_ID=<svc_account_access_key>
export AWS_SECRET_ACCESS_KEY=<svc_account_secret_access_key>
export INPUT_S3_BUCKET=enterprise-data-team
export INPUT_S3_KEY=projects/consumer-complaints/public/consumer_complaint_datashare.csv
export INPUT_S3_KEY_METADATA=projects/consumer-complaints/public/consumer_complaint_datashare_metadata.json
```

Then you can run `make elasticsearch` to mimic the production pipeline, but without uploading any files to s3 as the prod pipeline does.

Running the full production pipeline, with the bare command `make`, will upload seven large public files to s3.  
To test without overwriting the files created by the prod pipeline, you can export these env vars before running `make`:

```bash
export OUTPUT_S3_BUCKET=enterprise-data-team
export OUTPUT_S3_FOLDER=projects/consumer-complaints/internal_test/<YOUR INITIALS>
```

The commands `make` and `make elasticsearch` include a timestamp check, so if your local data files are up to date, the pipeline won't run.


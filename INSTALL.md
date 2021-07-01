# Local installation

### The CCDB repos

The CCDB project is broken into three repos, which is great for isolating code for indexing ([ccdb-data-pipeline](https://github.com/cfpb/ccdb-data-pipeline)), searching ([ccdb5-api](https://github.com/cfpb/ccdb5-api)), and user interface ([ccdb5-ui](https://github.com/cfpb/ccdb5-ui)). The public data are produced in a pipeline that begins with complaints stored in SalesForce and ends with a public CSV file, which is scrubbed of PII and updated on S3 every morning. The CSV is then indexed in our production Elasticsearch service.

The separation of concerns allows us to run the complaint pipeline from source to Elasticsearch without involving consumerfinance.gov code. But the separation makes it tricky to get a local development environment running with indexed data along with development versions of code from the various repos.

The first step is to create and activate a Python3 virtualenv, then clone and set up the project.

```bash
git clone https://github.com/cfpb/ccdb-data-pipeline.git
cd ccdb-data-pipeline
cp config_sample.ini config.ini
pip install -r requirements.txt
```

### A hybrid local setup
The next hurdle is how to get current complaint data loaded in local Elasticsearch and how to explore the resulting index.

Kibana is a great resource for exploring and troubleshooting Elasticsearch, but we don't have Kibana approved for our AWS Elasticsearch services. So running Kibana and Elasticsearch locally is attractive, and the easiest way to get them running together is in Docker.

We routinely run cfgov [in Docker](https://cfpb.github.io/consumerfinance.gov/running-docker/), but trying to run the full cfgov+ccdb stack in Docker can be time-consuming and tricky, in part because the indexing is not handled by cfgov code, and it's easy to get mismatched index names. It's also hard to get all the CCDB pieces installed with the correct combination of env variables, which are set when a container is built. Fixing env variables requires time-consuming Docker rebuilds, which carry the risk of losing data or indexes.

One useful option is to use Docker only for Elasticsearch. You can do this by spinning up a full suite of consumerfinance.gov docker containers with `docker-compose up`, and then run `docker-compose stop python postgres`. That way you can run postgres and python locally, test code, change env variables quickly, and set pdb traces that show up in the local runserver. Elasticsearch will be available at localhost:9200 and Kibana at <http://localhost:5601/app/dev_tools#/console>.

This setup assumes you have a working local consumerfinance.gov environment with postgres installed. Follow steps in the public cfgov setup docs for [standalone](https://cfpb.github.io/consumerfinance.gov/installation/#stand-alone-installation) and [docker](https://cfpb.github.io/consumerfinance.gov/installation/#stand-alone-installation) installation.

### Building your local index

For this step, you need to add these env variables:  
```bash
export ES_USERNAME=elasticsearch
export ES_PASSWORD=""
export ENV=dev
```

With your local Elasticsearch service running at localhost:9200, you can now run the `make` option that uses the public CCDB data files:

```bash
make from_public
```

The program downloads two public data files – a CSV of complaints and a json file of metadata – preps them for indexing, and indexes them in Elasticsearch.

After the index builds, you can confirm it in your local [Kibana console](<http://localhost:5601/app/dev_tools#/console>) with this command:


```bash
GET /_cat/indices
```

Kibana has some nice autocompletion helpers for testing queries and other uses of the Elasticsearch API.  
See the Kibana [console docs](https://www.elastic.co/guide/en/kibana/current/console-kibana.html) to dig deeper.

In the environment where cfgov is running, make sure these env vars are available so the search API is using the same index that the pipeline built:

```bash
export COMPLAINT_ES_INDEX=complaint-public-dev
export COMPLAINT_DOC_TYPE=complaint
```

You should now have a working [CCDB search app](http://localhost:8000/data-research/consumer-complaints/search/?dataNormalization=None&dateRange=3y&date_received_max=2021-06-17&date_received_min=2018-06-17&searchField=all&tab=Map) running with the latest data.


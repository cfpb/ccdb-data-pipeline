# JSON = [{}, {}, {}]
# "SOCRATA_JSON" = {metadata: {}, data: [[], [], []]}
# ND-JSON = {}\n{}\n{}\n

DIRS := complaints/ccdb/intake complaints/ccdb/ready_es complaints/ccdb/ready_s3
MAX_RECORDS := 0

# Aliases

ALIAS := complaint-public-$(ENV)

# File Targets

CONFIG_CCDB := config-ccdb.ini

DATASET_CSV := complaints/ccdb/intake/complaints.csv
DATASET_ND_JSON := complaints/ccdb/ready_es/complaints.json
DATASET_PUBLIC_CSV := complaints/ccdb/ready_s3/complaints.csv
DATASET_PUBLIC_JSON := complaints/ccdb/ready_s3/complaints.json

# Field Names

FIELDS_S3_CSV := complaints/ccdb/fields-s3-csv.txt
FIELDS_S3_JSON := complaints/ccdb/fields-s3-json.txt

# Sentinels

INDEX_CCDB := complaints/ccdb/ready_es/.last_indexed
INPUT_S3_TIMESTAMP := complaints/ccdb/intake/.latest_dataset
PUSH_S3 := complaints/ccdb/ready_s3/.last_pushed

# Defaults

ALL_LIST=$(INDEX_CCDB) $(PUSH_S3)

# -----------------------------------------------------------------------------
# Environment specific configuration

ifeq ($(ENV), dev)
	PY := python
	MAX_RECORDS := 80001
else ifeq ($(ENV), staging)
	PY := .py/bin/python
else ifeq ($(ENV), prod)
	PY := .py/bin/python
else
	$(error "must specify ENV={dev, staging, prod}")
	exit 1;
endif

# -----------------------------------------------------------------------------
# Action Targets

all: dirs check_latest $(ALL_LIST)

check_latest:
	# checking to see if there is a new dataset
	$(PY) -m complaints.ccdb.acquire --check-latest -c $(CONFIG_CCDB) -o $(INPUT_S3_TIMESTAMP)

clean:
	for dir in $(DIRS) ; do rm -rf $$dir ; done

dirs:
	for dir in $(DIRS) ; do [ -d $$dir ] || mkdir -p $$dir ; done

ls_in:
	$(eval FOLDER=$(shell dirname $$INPUT_S3_KEY))
	aws s3 ls --recursive "s3://$$INPUT_S3_BUCKET/$(FOLDER)"

ls_out:
	aws s3 ls --recursive "s3://$$OUTPUT_S3_BUCKET/$$OUTPUT_S3_FOLDER"

# -----------------------------------------------------------------------------
# Asset Targets

$(INDEX_CCDB): complaints/ccdb/ccdb_mapping.json $(DATASET_ND_JSON) $(CONFIG_CCDB)
	$(PY) -m complaints.ccdb.index_ccdb -c $(CONFIG_CCDB) \
	   --dataset $(DATASET_ND_JSON) --index-name $(ALIAS)
	$(PY) -m complaints.taxonomy.index_taxonomy -c $(CONFIG_CCDB) \
	   --taxonomy complaints/taxonomy/taxonomy.txt --index-name $(ALIAS)
	touch $@

$(PUSH_S3): $(DATASET_PUBLIC_CSV) $(DATASET_PUBLIC_JSON)
	$(PY) -m complaints.ccdb.push_s3 -c $(CONFIG_CCDB) $(DATASET_PUBLIC_JSON)
	$(PY) -m complaints.ccdb.push_s3 -c $(CONFIG_CCDB) $(DATASET_PUBLIC_CSV)
	touch $@

$(CONFIG_CCDB):
	cp config_sample.ini $(CONFIG_CCDB)

$(DATASET_CSV): $(INPUT_S3_TIMESTAMP)
	$(PY) -m complaints.ccdb.acquire -c $(CONFIG_CCDB) -o $@

$(DATASET_ND_JSON): $(DATASET_CSV) $(FIELDS_S3_JSON)
	$(PY) common/csv2json.py --limit $(MAX_RECORDS) --json-format NDJSON \
	                         --fields $(FIELDS_S3_JSON) $< $@

$(DATASET_PUBLIC_CSV): $(DATASET_CSV) $(FIELDS_S3_CSV)
	cp $< $@
	$(eval FIELDS=$(shell cat $(FIELDS_S3_CSV) | tr '\n' ','))
	@# Replace first line of CSV with expected column names
	@# https://stackoverflow.com/a/13438118
	sed -i '' "1s/.*/$(FIELDS)/" $@

$(DATASET_PUBLIC_JSON): $(DATASET_CSV) $(FIELDS_S3_JSON)
	$(PY) common/csv2json.py --limit $(MAX_RECORDS) --json-format JSON \
	                         --fields $(FIELDS_S3_JSON) $< $@
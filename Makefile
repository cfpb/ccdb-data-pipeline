OS_NAME := $(shell uname -s | tr A-Z a-z)

# JSON = [{}, {}, {}]
# "SOCRATA_JSON" = {metadata: {}, data: [[], [], []]}
# ND-JSON = {}\n{}\n{}\n

DIRS := complaints/ccdb/intake complaints/ccdb/ready_es complaints/ccdb/ready_s3
MAX_RECORDS ?= 0

# Aliases

ALIAS := complaint-public-$(ENV)

# File Targets

CONFIG_CCDB := config-ccdb.ini

DATASET_CSV := complaints/ccdb/intake/complaints.csv
DATASET_ND_JSON := complaints/ccdb/ready_es/complaints.json
DATASET_PUBLIC_CSV := complaints/ccdb/ready_s3/complaints.csv
DATASET_PUBLIC_JSON := complaints/ccdb/ready_s3/complaints.json

METADATA_JAVASCRIPT := complaints/ccdb/ready_s3/metadata.js
METADATA_JSON := complaints/ccdb/intake/complaints_metadata.json
METADATA_PUBLIC_JSON := complaints/ccdb/ready_s3/complaints_metadata.json

# Field Names

FIELDS_S3_CSV := complaints/ccdb/intake/fields-s3-csv.txt
FIELDS_S3_JSON := complaints/ccdb/intake/fields-s3-json.txt

# Sentinels

INDEX_CCDB := complaints/ccdb/ready_es/.last_indexed
INPUT_S3_TIMESTAMP := complaints/ccdb/intake/.latest_dataset
PUSH_S3 := complaints/ccdb/ready_s3/.last_pushed

# URLs

URL_PUBLIC_CSV ?= https://files.consumerfinance.gov/ccdb/complaints.csv
URL_PUBLIC_METADATA ?= https://files.consumerfinance.gov/ccdb/complaints_metadata.json

# Verification

S3_JSON_COUNT := complaints/ccdb/verification/json_prev_size.txt
AKAMAI_CACHE_COUNT := complaints/ccdb/verification/cache_prev_size.txt

# Defaults

ALL_LIST=$(PUSH_S3) $(INDEX_CCDB)

# -----------------------------------------------------------------------------
# Environment specific configuration

ifeq ($(ENV), local)
	PY := python
	MAX_RECORDS := 80001
else ifeq ($(ENV), dev)
	PY := python
else ifeq ($(ENV), staging)
	PY := python
else ifeq ($(ENV), prod)
	PY := python
	ALIAS := complaint-public
else
	$(error "must specify ENV={local, dev, staging, prod}")
	exit 1;
endif

# -----------------------------------------------------------------------------
# Action Targets

all: dirs check_latest $(ALL_LIST)

check_latest: dirs $(CONFIG_CCDB)
	# checking to see if there is a new dataset
	$(PY) -m complaints.ccdb.acquire --check-latest -c $(CONFIG_CCDB) -o $(INPUT_S3_TIMESTAMP)

clean:
	for dir in $(DIRS) ; do rm -rf $$dir ; done

dirs:
	for dir in $(DIRS) ; do [ -d $$dir ] || mkdir -p $$dir ; done

elasticsearch: dirs check_latest $(INDEX_CCDB)


from_public: dirs
	@# This will get the date modified header: curl -L -sI $(URL_PUBLIC_CSV)
	touch $(INPUT_S3_TIMESTAMP)
	curl -L -o $(DATASET_CSV) $(URL_PUBLIC_CSV)
	curl -L -o $(METADATA_JSON) $(URL_PUBLIC_METADATA)
	$(MAKE) $(INDEX_CCDB)

ls_in:
	$(eval FOLDER=$(shell dirname $$INPUT_S3_KEY))
	aws s3 ls --recursive "s3://$$INPUT_S3_BUCKET/$(FOLDER)"

ls_out:
	aws s3 ls --recursive "s3://$$OUTPUT_S3_BUCKET/$$OUTPUT_S3_FOLDER"

s3: dirs check_latest $(PUSH_S3)

verify_s3: verify_s3


# -----------------------------------------------------------------------------
# Asset Targets

.DELETE_ON_ERROR :

$(INDEX_CCDB): complaints/ccdb/ccdb_mapping.json $(DATASET_ND_JSON) $(METADATA_JSON) $(CONFIG_CCDB)
	$(PY) -m complaints.ccdb.index_ccdb -c $(CONFIG_CCDB) \
	   --dataset $(DATASET_ND_JSON) \
	   --metadata $(METADATA_JSON) \
	   --index-name $(ALIAS)
	touch $@

$(PUSH_S3): $(DATASET_PUBLIC_CSV) $(DATASET_PUBLIC_JSON) $(METADATA_PUBLIC_JSON) $(METADATA_JAVASCRIPT)
	$(PY) -m complaints.ccdb.push_s3 -c $(CONFIG_CCDB) $(DATASET_PUBLIC_JSON)
	$(PY) -m complaints.ccdb.push_s3 -c $(CONFIG_CCDB) --no-zip $(DATASET_PUBLIC_JSON)
	$(PY) -m complaints.ccdb.push_s3 -c $(CONFIG_CCDB) $(DATASET_PUBLIC_CSV)
	$(PY) -m complaints.ccdb.push_s3 -c $(CONFIG_CCDB) --no-zip $(DATASET_PUBLIC_CSV)
	$(PY) -m complaints.ccdb.push_s3 -c $(CONFIG_CCDB) --no-zip $(METADATA_PUBLIC_JSON)
	$(PY) -m complaints.ccdb.push_s3 -c $(CONFIG_CCDB) --no-zip $(METADATA_JAVASCRIPT)
	touch $@

verify_s3: $(CONFIG_CCDB)
	$(PY) -m complaints.ccdb.verify_s3 -c $(CONFIG_CCDB) $(DATASET_PUBLIC_JSON) $(S3_JSON_COUNT) $(AKAMAI_CACHE_COUNT)

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
	@#
	@# But MacOS and GNU have slightly different syntax
	@# https://stackoverflow.com/a/57766728
ifeq ($(OS_NAME),darwin)
	sed -i '' -e '1s/.*/$(FIELDS)/' $@
else
	sed -i -e '1s/.*/$(FIELDS)/' $@
endif

$(DATASET_PUBLIC_JSON): $(DATASET_CSV) $(FIELDS_S3_JSON)
	$(PY) common/csv2json.py --limit $(MAX_RECORDS) --json-format JSON \
	                         --fields $(FIELDS_S3_JSON) $< $@

$(FIELDS_S3_CSV): $(DATASET_CSV)
	$(PY) -m complaints.ccdb.choose_field_map --target-format CSV $< $@

$(FIELDS_S3_JSON): $(DATASET_CSV)
	$(PY) -m complaints.ccdb.choose_field_map --target-format JSON $< $@

$(METADATA_JAVASCRIPT): $(METADATA_PUBLIC_JSON)
	$(PY) -m complaints.ccdb.build_metadata_javascript $< $@

$(METADATA_JSON): $(INPUT_S3_TIMESTAMP)
	$(PY) -m complaints.ccdb.acquire -c $(CONFIG_CCDB) \
	      -k $(INPUT_S3_KEY_METADATA) \
	      -o $@

$(METADATA_PUBLIC_JSON): $(METADATA_JSON)
	$(PY) -m complaints.ccdb.scrub_metadata $< $@

# JSON = [{}, {}, {}]
# "SOCRATA_JSON" = {metadata: {}, data: [[], [], []]}
# ND-JSON = {}\n{}\n{}\n

MAX_RECORDS=0

# Aliases

ALIAS=complaint-public-$(ENV)

# File Targets

CONFIG_CCDB=config-ccdb.ini

DATASET_CSV=complaints/ccdb/consumer_complaint_datashare.csv
DATASET_ND_JSON=complaints/ccdb/ccdb_output.json

# Sentinels

SENTINEL_CCDB=complaints/ccdb/.last_indexed

# Defaults

ALL_LIST=$(SENTINEL_CCDB)
ALL_FILE_TARGETS=$(DATASET_CSV) $(DATASET_ND_JSON) $(SENTINEL_CCDB)

# -----------------------------------------------------------------------------
# Environment specific configuration

ifeq ($(ENV), dev)
	PY=python
	MAX_RECORDS=20001
else ifeq ($(ENV), staging)
	PY=.py/bin/python
else ifeq ($(ENV), prod)
	PY=.py/bin/python
else
	$(error "must specify ENV={dev, staging, prod}")
	exit 1;
endif

# -----------------------------------------------------------------------------
# Action Targets

all: $(ALL_LIST)

clean:
	rm -rf $(ALL_FILE_TARGETS)

# -----------------------------------------------------------------------------
# Asset Targets

$(SENTINEL_CCDB): complaints/ccdb/ccdb_mapping.json $(DATASET_ND_JSON) $(CONFIG_CCDB)
	$(PY) -m complaints.ccdb.index_ccdb -c $(CONFIG_CCDB) \
	   --dataset $(DATASET_ND_JSON) --index-name $(ALIAS)
	$(PY) -m complaints.taxonomy.index_taxonomy -c $(CONFIG_CCDB) \
	   --taxonomy complaints/taxonomy/taxonomy.txt --index-name $(ALIAS)
	touch $@

$(CONFIG_CCDB):
	cp config_sample.ini $(CONFIG_CCDB)

$(DATASET_CSV):
	$(PY) -m complaints.ccdb.acquire -c $(CONFIG_CCDB) -o $@

$(DATASET_ND_JSON): $(DATASET_CSV)
	$(PY) common/csv2json.py --limit $(MAX_RECORDS) --json-format NDJSON $< $@

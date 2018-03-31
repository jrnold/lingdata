RSCRIPT ?= RScript
SQLITE ?= sqlite3
PYTHON ?= python3
LINGDATA_S3_BUCKET ?= s3://jrnold-data/lingdata/

all: build

DB = wals glottolog asjp iso_639_3 ethnologue

build: $(DB)
.PHONY: build

#### WALS ####

wals: data/wals.db
.PHONY: wals

data/wals.db: bin/wals.R src/wals.sql data-raw/wals-updates.csv
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(RSCRIPT) $< $@

#### ASJP Data ####

asjp: data/asjp.db
.PHONY: asjp

data/asjp.db: lingdata/asjp.py lingdata/utils.py src/asjp.sql data-raw/ASJP_meanings.json
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(PYTHON) -m lingdata.asjp $@


#### Glottolog Data ####

glottolog: data/glottolog.db
.PHONY: glottolog

data/glottolog.db: lingdata/glottolog.py lingdata/utils.py src/glottolog.sql
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(PYTHON) -m lingdata.glottolog $@


#### ISO 639-3 Data ####

iso_639_3: data/iso_639_3.db
.PHONY: iso_639_3

data/iso_639_3.db: lingdata/iso_639_3.py lingdata/utils.py src/iso_639_3.sql
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(PYTHON) -m lingdata.iso_639_3 $@


#### Ethnologue Data ####

ethnologue: data/ethnologue.db
.PHONY: ethnologue

data/ethnologue.db: lingdata/ethnologue.py lingdata/utils.py src/ethnologue.sql
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(PYTHON) -m lingdata.ethnologue $@


#### Dump databases ####

dump: $(DB:%=data/%.sql.gz)
.PHONY: dump

data/%.sql.gz: data/%.db
	sqlite3 $< .dump | gzip -c > $@


#### Push data to S3 ####

dist: dump
	aws s3 sync data/ $(LINGDATA_S3_BUCKET)
.PHONY: dist

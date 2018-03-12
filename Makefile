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

data/asjp.db: bin/asjp.py src/asjp.sql data-raw/ASJP_meanings.json
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(PYTHON) $< $@


#### Glottolog Data ####

glottolog: data/glottolob.db
.PHONY: glottolog

data/glottolog.db: bin/glottolog.py src/glottolog.sql
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(PYTHON) $< $@


#### ISO 639-3 Data ####

iso_639_3: data/iso_639_3.db
.PHONY: iso_639_3

data/iso_639_3.db: bin/iso_639_3.py src/iso_639_3.sql
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(PYTHON) $< $@


#### Ethnologue Data ####

ethnologue: data/ethnologue.db
.PHONY: ethnologue

data/ethnologue.db: bin/ethnologue.py src/ethnologue.sql
	-rm -f $@
	$(SQLITE) $@ < $(filter %.sql,$^)
	$(PYTHON) $< $@


#### Dump databases ####

dump: $(DB:%=dumps/%.sql.gz)
.PHONY: dump

data/%.sql.gz: data/%.db
	sqlite3 $< .dump | gzip -c > $@


#### Push data to S3 ####

dist: dump
	aws s3 sync dumps/ $(LINGDATA_S3_BUCKET)
.PHONY: dist

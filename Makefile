LINGDATA_S3_BUCKET ?= s3://jrnold-data/lingdata/

all: build

DB = wals glottolog asjp iso_639_3 ethnologue

build: $(DB)
.PHONY: build

wals:
	make -C wals
.PHONY: wals

asjp:
	make -C asjp
.PHONY: asjp

glottolog:
	make -C glottolog
.PHONY: glottolog

iso_639_3:
	make -C iso_639_3
.PHONY: iso_639_3

ethnologue:
	make -C ethnologue
.PHONY: ethnologue

dump: $(DB:%=dumps/%.sql.gz)
.PHONY: dump

dumps/wals.sql.gz: wals/wals.db
	sqlite3 $< .dump | gzip -c > $@

dumps/asjp.sql.gz: asjp/asjp.db
	sqlite3 $< .dump | gzip -c > $@

dumps/iso_639_3.sql.gz: iso_639_3/iso_639_3.db
	sqlite3 $< .dump | gzip -c > $@

dumps/glottolog.sql.gz: glottolog/glottolog.db
	sqlite3 $< .dump | gzip -c > $@

dumps/ethnologue.sql.gz: ethnologue/ethnologue.db
	sqlite3 $< .dump | gzip -c > $@


dist: dump
	aws s3 sync dumps/ $(LINGDATA_S3_BUCKET)
.PHONY: dist

LINGDATA_S3_BUCKET ?= s3://jrnold-data/lingdata/

DB = wals glottolog asjp iso_639_3 ethnologue

all: build
.PHONY: all

build:
	for dir in $(DB); do \
		make -C $$dir build; \
	done
.PHONY: build

dump: $(patsubst %,dumps/%.sql.gz,$(DB))
.PHONY: dump

dumps/wals.sql.gz: wals/wals.db
dumps/glottolog.sql.gz: glottolog/glottolog.db
dumps/iso_639_3.sql.gz: iso_639_3/iso_639_3.db
dumps/ethnologue.sql.gz: ethnologue/ethnologue.db
dumps/asjp.sql.gz: asjp/asjp.db

%.sql.gz: %.db
	sqlite3 $< .dump | gzip -c > $@


dist: dump
	aws s3 sync dumps/ $(LINGDATA_S3_BUCKET)
.PHONY: dist

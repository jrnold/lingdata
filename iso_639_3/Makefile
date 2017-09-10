PYTHON ?= python

all: build
.PHONY: all

build: iso_639_3.db
.PHONY: build

iso_639_3.db: iso-639-3-tables.sql iso_639_3.py
	-rm $@
	sqlite3 $@ < $(filter %.sql,$^)
	$(PYTHON) $(filter %.py,$^)

dump: iso_639_3.sql.gz
.PHONY: dump

iso_639_3.sql.gz: iso_639_3.db
	sqlite3 $< .dump | gzip -c > $@

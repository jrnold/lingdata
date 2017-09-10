PYTHON ?= python

all: build
.PHONY: all

build: ethnologue.db iso_639_3.db
.PHONY: build

ethnologue.db: ethnologue.sql ethnologue.py
	-rm $@
	sqlite3 $@ < $<
	$(PYTHON) ethnologue.py

iso_639_3.db: iso-639-3.sql iso_639_3.py
	-rm $@
	sqlite3 $@ < $<
	$(PYTHON) iso_639_3.py

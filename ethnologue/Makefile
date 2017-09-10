PYTHON ?= python

all: build
.PHONY: all

build: ethnologue.db
.PHONY: build

ethnologue.db: ethnologue.sql ethnologue.py
	-rm $@
	sqlite3 $@ < $(filter %.sql,$^)
	$(PYTHON) $(filter %.py,$^)

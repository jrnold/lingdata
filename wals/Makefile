RSCRIPT ?= RScript

all: build
.PHONY: all

build: wals.db
.PHONY: build

wals.db: wals.R wals-updates.csv wals-tables.sql
	-rm $@
	sqlite3 $@ < wals-tables.sql
	$(RSCRIPT) $<

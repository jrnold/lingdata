RSCRIPT ?= RScript

all: build
.PHONY: all

build: wals.db
.PHONY: build

wals.db: wals.R wals-updates.csv wals.sql
	$(RSCRIPT) $<

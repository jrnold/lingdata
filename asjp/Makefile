PYTHON ?= python

all: build
.PHONY: all

build: asjp.db
.PHONY: build

asjp.db: asjp.py ASJP_meanings.json
	$(PYTHON) $<

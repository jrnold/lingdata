PYTHON ?= python

all: build
.PHONY: all

build: glottolog-tree.json glottolog.db
.PHONY: build

glottolog-tree.json: glottolog-tree.py
	$(PYTHON) $< > $@

glottolog.db: glottolog.py glottolog-tree.json
	$(PYTHON) $<

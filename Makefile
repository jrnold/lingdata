all: build
.PHONY: all

build: wals glottolog asjp iso639
.PHONY: build

wals:
	make -C wals
.PHONY: wals

glottolog:
	make -C glottolog
.PHONY: glottolog

asjp:
	make -C asjp
.PHONY: asjp

iso639:
  make -C iso639
.PHONY: iso639

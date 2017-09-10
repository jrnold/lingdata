all: build
.PHONY: all

build: wals glottolog asjp
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

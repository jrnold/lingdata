-- DDL for glottolog.db
CREATE TABLE languoids (
    glottocode CHAR(8) NOT NULL PRIMARY KEY,
    name CHAR,
    latitude REAL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL CHECK (longitude BETWEEN -180 AND 180),
    level TEXT CHECK (level IN ('family', 'language', 'dialect')),
    status TEXT,
    bookkeeping BOOLEAN,
    parent_id CHAR(8),
    family_id CHAR(8),
    child_family_count INT,
    child_language_count INT,
    child_dialect_count INT,
    depth INT CHECK (depth > 0),
    subtree_depth INT CHECK (subtree_depth >= 0)
);
CREATE TABLE paths (
    glottocode CHAR(8),
    glottocode_to CHAR(8),
    dist INT CHECK (dist != 0), -- can be negative or positive
    PRIMARY KEY (glottocode, glottocode_to),
        FOREIGN KEY (glottocode) REFERENCES languoids (glottocode),
    FOREIGN KEY (glottocode_to) REFERENCES languoids (glottocode)
);
CREATE TABLE distances (
    glottocode_1 CHAR(8),
    glottocode_2 CHAR(8),
    shared INT CHECK (shared >= 0),
    geo REAL CHECK (geo >= 0),
    PRIMARY KEY (glottocode_1, glottocode_2),
    FOREIGN KEY (glottocode_1) REFERENCES languoids (glottocode),
    FOREIGN KEY (glottocode_2) REFERENCES languoids (glottocode)
);
CREATE TABLE wals_codes (
    glottocode CHAR(8) NOT NULL,
    wals_code CHAR(3) NOT NULL,
    FOREIGN KEY (glottocode) REFERENCES languoids (glottocode)
);
CREATE TABLE iso_codes (
    glottocode CHAR(8) NOT NULL,
    iso_639_3 CHAR(3) NOT NULL,
    FOREIGN KEY (glottocode) REFERENCES languoids (glottocode)
);
CREATE TABLE countries (
    glottocode CHAR(8) NOT NULL,
    country_code CHAR(2) NOT NULL,
    FOREIGN KEY (glottocode) REFERENCES languoids (glottocode)
);
CREATE TABLE macroareas (
    glottocode CHAR(8) NOT NULL,
    macroarea TEXT NOT NULL,
    FOREIGN KEY (glottocode) REFERENCES languoids (glottocode)
);

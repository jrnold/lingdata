-- DDL for wals.db
CREATE TABLE families (
    family TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE genuses (
    genus TEXT NOT NULL PRIMARY KEY,
    family TEXT NOT NULL,
    FOREIGN KEY (family) REFERENCES families (family)
);

CREATE TABLE macroareas (
    macroarea TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE languages (
    wals_code CHAR(3) PRIMARY KEY,
    iso_code CHAR(3),
    glottocode CHAR(8),
    Name TEXT NOT NULL,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    genus TEXT NOT NULL,
    family TEXT NOT NULL,
    macroarea TEXT NOT NULL,
    FOREIGN KEY (genus) REFERENCES genuses (genus),
    FOREIGN KEY (family) REFERENCES families (family),
    FOREIGN KEY (macroarea) REFERENCES macroareas (macroarea)
);

CREATE TABLE language_countries (
    wals_code CHAR(3),
    countrycode CHAR(2),
    FOREIGN KEY (wals_code) REFERENCES languages (wals_code)
);

CREATE TABLE features (
    feature_id CHAR(4) PRIMARY KEY,
    feature_name TEXT,
    area TEXT
);

CREATE TABLE feature_values (
    feature_id CHAR(4) NOT NULL,
    value INT NOT NULL CHECK (value > 0),
    label TEXT NOT NULL,
    PRIMARY KEY (feature_id, value),
    FOREIGN KEY (feature_id) REFERENCES features (feature_id)
);

CREATE TABLE language_features (
    wals_code CHAR(3) NOT NULL,
    feature_id CHAR(4) NOT NULL,
    value INT NOT NULL CHECK (value > 0),
    PRIMARY KEY (wals_code, feature_id),
    FOREIGN KEY (wals_code) REFERENCES languages (wals_code),
    FOREIGN KEY (feature_id) REFERENCES features (feature_id),
    FOREIGN KEY (feature_id, value) REFERENCES feature_values (feature_id, value)
);

CREATE TABLE distances (
    wals_code_1 CHAR(3) NOT NULL,
    wals_code_2 CHAR(3) NOT NULL,
    -- at least one feature shuld be non-missing, but
    variable TEXT NOT NULL,
    value REAL NOT NULL CHECK (value >= 0),
    PRIMARY KEY (wals_code_1, wals_code_2, variable),
    FOREIGN KEY (wals_code_1) REFERENCES languages (wals_code),
    FOREIGN KEY (wals_code_2) REFERENCES languages (wals_code),
    CHECK (wals_code_1 < wals_code_2)
);

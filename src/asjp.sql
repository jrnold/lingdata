--  DDL for asjp.db
CREATE TABLE meanings (
    meaning TEXT PRIMARY KEY,
    num INTEGER UNIQUE,
    in_forty BOOLEAN NOT NULL
);

CREATE TABLE languages (
    language TEXT PRIMARY KEY,
    wls_fam TEXT NOT NULL,
    wls_gen TEXT NOT NULL,
    e TEXT,
    hh TEXT,
    lat NUMERIC CHECK (lat BETWEEN -90 AND 90),
    lon NUMERIC CHECK (lon BETWEEN -180 AND 180),
    pop INTEGER CHECK (pop >= 0),
    wcode CHAR(3),
    iso CHAR(3)
);

CREATE TABLE wordlists (
    language TEXT NOT NULL,
    meaning TEXT NOT NULL,
    word TEXT NOT NULL,
    synonym_num INTEGER CHECK (synonym_num >= 1),
    loanword BOOLEAN NOT NULL,
    PRIMARY KEY (language, meaning, word),
    FOREIGN KEY (language) REFERENCES languages (language),
    FOREIGN KEY (meaning) REFERENCES meanings (meaning)
);

CREATE TABLE distances (
    language_1 TEXT NOT NULL,
    language_2 TEXT NOT NULL,
    ldn NUMERIC NOT NULL CHECK (ldn BETWEEN 0 AND 1),
    ldnd NUMERIC NOT NULL CHECK (ldnd >= 0),
    common_words INTEGER NOT NULL CHECK (common_words >= 1),
    PRIMARY KEY (language_1, language_2),
    FOREIGN KEY (language_2) REFERENCES languages (language),
    FOREIGN KEY (language_1) REFERENCES languages (language)
);

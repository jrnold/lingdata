-- See http://www-01.sil.org/iso639-3/download.asp
CREATE TABLE LangTypes (
  Type char(1) NOT NULL,
  Description varchar NOT NULL,
  PRIMARY KEY (Type)
);
INSERT INTO LangTypes VALUES ("A", "Ancient");
INSERT INTO LangTypes VALUES ("C", "Constructed");
INSERT INTO LangTypes VALUES ("L", "Living");
INSERT INTO LangTypes VALUES ("H", "Historical");
INSERT INTO LangTypes VALUES ("X", "Extinct");
INSERT INTO LangTypes VALUES ("S", "Special");

CREATE TABLE LangScopes (
  Scope char(1) NOT NULL,
  Description varchar NOT NULL,
  PRIMARY KEY (Scope)
);
INSERT INTO LangScopes VALUES ("I", "Individual");
INSERT INTO LangScopes VALUES ("M", "Macrolanguage");
INSERT INTO LangScopes VALUES ("S", "Special");

CREATE TABLE iso_639_3 (
  Id      char(3) NOT NULL,  -- The three-letter 639-3 identifier
  Part2B  char(3) NULL,      -- Equivalent 639-2 identifier of the bibliographic applications
                            -- code set, if there is one
  Part2T  char(3) NULL,      -- Equivalent 639-2 identifier of the terminology applications code
                            -- set, if there is one
  Part1   char(2) NULL,      -- Equivalent 639-1 identifier, if there is one
  Scope   char(1) NOT NULL,  -- I(ndividual), M(acrolanguage), S(pecial)
  Language_Type    char(1) NOT NULL,  -- A(ncient), C(onstructed),
                            -- E(xtinct), H(istorical), L(iving), S(pecial)
  Ref_Name   varchar NOT NULL,   -- Reference language name
  Comment    varchar NULL,
  PRIMARY KEY (Id),
  FOREIGN KEY (Scope) REFERENCES LangScopes (Scope),
  FOREIGN KEY (Language_Type) REFERENCES LangTypes (Type)
);

CREATE TABLE iso_639_3_Name_Index (
  Id             char(3) NOT NULL,  -- The three-letter 639-3 identifier
  Print_Name     varchar NOT NULL,  -- One of the names associated with this identifier
  Inverted_Name  varchar NOT NULL,
  PRIMARY KEY (Id, Print_Name),
  FOREIGN KEY (Id) REFERENCES iso_639_3 (Id)
);

CREATE TABLE LangStatuses (
  Status CHAR(1) NOT NULL PRIMARY KEY,
  Description VARCHAR
);
INSERT INTO LangStatuses VALUES ("A", "active");
INSERT INTO LangStatuses VALUES ("R", "retired");

CREATE TABLE iso_639_3_macrolanguages (
  M_Id      char(3) NOT NULL,   -- The identifier for a macrolanguage
  I_Id      char(3) NOT NULL,   -- The identifier for an individual language
                               -- that is a member of the macrolanguage
  I_Status  char(1) NOT NULL,   -- A (active) or R (retired) indicating the
                               -- status of the individual code element
  PRIMARY KEY (M_Id, I_Id),
  FOREIGN KEY (M_Id) REFERENCES iso_639_3 (Id),
  FOREIGN KEY (I_Id) REFERENCES iso_639_3 (Id),
  FOREIGN KEY (I_Status) REFERENCES LangStatuses (Status)
);

CREATE TABLE iso_639_3_Retirements (
  Id          char(3)      NOT NULL,     -- The three-letter 639-3 identifier
  Ref_Name    varchar      NOT NULL,     -- reference name of language
  Ret_Reason  char(1)      NOT NULL,     -- code for retirement: C (change), D (duplicate),
                                        -- N (non-existent), S (split), M (merge)
  Change_To   char(3)      NULL,         -- in the cases of C, D, and M, the identifier
                                        -- to which all instances of this Id should be changed
  Ret_Remedy  varchar      NULL,         -- The instructions for updating an instance
                                        -- of the retired (split) identifier
  Effective   date         NOT NULL,      -- The date the retirement became effective
  PRIMARY KEY (Id)
);

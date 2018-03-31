-- DDL for ethnologue.db
-- Adapted from https://www.ethnologue.com/codes/code-table-structure
CREATE TABLE CountryCodes (
   CountryID  CHAR(2) NOT NULL,  -- Two-letter code from ISO3166
   Name   VARCHAR NOT NULL,  -- Country name
   Area   VARCHAR NOT NULL,
   PRIMARY KEY (CountryID)
);

CREATE TABLE LangStatuses (
   LangStatus CHAR(1) NOT NULL PRIMARY KEY,
   Label VARCHAR NOT NULL
);
INSERT INTO LangStatuses VALUES ("L", "Living");
INSERT INTO LangStatuses VALUES ("X", "Extinct");

CREATE TABLE LanguageCodes (
   LangID      CHAR(3) NOT NULL,  -- Three-letter code
   CountryID   CHAR(2) NOT NULL,  -- Main country where used
   LangStatus  CHAR(1) NOT NULL,  -- L(iving), (e)X(tinct)
   Name    TEXT NOT NULL,
   PRIMARY KEY (LangID),
   FOREIGN KEY (CountryID) REFERENCES CountryCodes (CountryID),
   FOREIGN KEY (LangStatus) REFERENCES LangStatuses (LangStatus)
);

CREATE TABLE NameTypes (
   NameType CHAR(1) NOT NULL PRIMARY KEY,
   Label VARCHAR NOT NULL
);
INSERT INTO NameTypes VALUES ("L", "Language");
INSERT INTO NameTypes VALUES ("LA", "Language Alternate");
INSERT INTO NameTypes VALUES ("D", "Dialect");
INSERT INTO NameTypes VALUES ("DA", "Dialect Alternate");
INSERT INTO NameTypes VALUES ("LP", "Language Pejorative");
INSERT INTO NameTypes VALUES ("DP", "Dialect Pejorative");

CREATE TABLE LanguageIndex (
   LangID    CHAR(3) NOT NULL,
   CountryID CHAR(2) NOT NULL,
   NameType  CHAR(2) NOT NULL,
   -- Some are null for whatever reason
   Name  VARCHAR,
   PRIMARY KEY (LangID, CountryID, NameType, Name),
   FOREIGN KEY (CountryID) REFERENCES CountryCodes (CountryID),
   FOREIGN KEY (LangID) REFERENCES LanguageCode (LangID),
   FOREIGN KEY (NameType) REFERENCES NameTypes (NameType)
);

-- DDL for iso_639_3.db
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
  Id      char(3) NOT NULL,
  Part2B  char(3) NULL,
  Part2T  char(3) NULL,
  Part1   char(2) NULL,
  Scope   char(1) NOT NULL,
  Language_Type    char(1) NOT NULL,
  Ref_Name   varchar NOT NULL,
  Comment    varchar NULL,
  PRIMARY KEY (Id),
  FOREIGN KEY (Scope) REFERENCES LangScopes (Scope),
  FOREIGN KEY (Language_Type) REFERENCES LangTypes (Type)
);

CREATE TABLE iso_639_3_Name_Index (
  Id             char(3) NOT NULL,
  Print_Name     varchar NOT NULL,
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
  M_Id      char(3) NOT NULL,
  I_Id      char(3) NOT NULL,
  I_Status  char(1) NOT NULL,
  PRIMARY KEY (M_Id, I_Id),
  FOREIGN KEY (M_Id) REFERENCES iso_639_3 (Id),
  FOREIGN KEY (I_Id) REFERENCES iso_639_3 (Id),
  FOREIGN KEY (I_Status) REFERENCES LangStatuses (Status)
);

CREATE TABLE Ret_Reasons (
  Ret_Reason char(1) NOT NULL PRIMARY KEY,
  Description varchar NOT NULL
);
INSERT INTO Ret_Reasons VALUES ("C", "Change");
INSERT INTO Ret_Reasons VALUES ("D", "Duplicate");
INSERT INTO Ret_Reasons VALUES ("N", "Non-existant");
INSERT INTO Ret_Reasons VALUES ("S", "Split");
INSERT INTO Ret_Reasons VALUES ("M", "Merge");

CREATE TABLE iso_639_3_Retirements (
  Id          char(3)      NOT NULL,
  Ref_Name    varchar      NOT NULL,
  Ret_Reason  char(1)      NOT NULL,
  Change_To   char(3)      NULL,
  Ret_Remedy  varchar      NULL,
  Effective   date         NOT NULL,
  PRIMARY KEY (Id),
  FOREIGN KEY (Ret_Reason) REFERENCES Ret_Reasons (Ret_Reason)
);

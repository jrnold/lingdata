#!/usr/bin/env python3
"""Download, process, and insert ISO 639-3 code tables into a database."""
import argparse
import io
import re
import sqlite3
import zipfile

import pandas as pd
import requests

CURRENT_DATE = "20170217"

URL = ("http://www-01.sil.org/iso639-3/"
       f"iso-639-3_Code_Tables_{CURRENT_DATE}.zip")

REGEXEN = (
    ("iso_639_3", r".*/iso-639-3_(\d+).tab"),
    ("iso_639_3_macrolanguages", r".*/iso-639-3-macrolanguages_(\d+)\.tab"),
    ("iso_639_3_Name_Index", r".*/iso-639-3_Name_Index_(\d+)\.tab"),
    ("iso_639_3_Retirements", r".*/iso-639-3_Retirements_(\d+)\.tab"))
""" Regular expresssions for the tsv file associated with each table """


def table2files(z):
    """Get the names of the files in the zipfile.

    This function is needed since the filenames have dates.
    """
    tables = []
    for tbl, pattern in REGEXEN:
        for f in z.infolist():
            m = re.search(pattern, f.filename)
            if m:
                print(f.filename)
                tables.append((tbl, f.filename))
                continue
    return tables


def insert_data(db):
    """Insert data from the ISO 639-3 zipfile into the database."""
    conn = sqlite3.connect(db)
    r = requests.get(URL, stream=True)
    z = zipfile.ZipFile(io.BytesIO(r.content), 'r')
    for tbl, filename in table2files(z):
        with io.TextIOWrapper(z.open(filename, 'r')) as f:
            # important to adjust NA values otherwise Namibia is problematic
            dat = pd.read_csv(f, delimiter='\t', na_values="",
                              keep_default_na=False)
            dat.to_sql(tbl, conn, if_exists='append', index=False)
    conn.commit()
    conn.close()


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="Path to SQLite database.")
    args = parser.parse_arguments()
    insert_data(args.db)


if __name__ == '__main__':
    main()

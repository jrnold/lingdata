#!/usr/bin/env python3
"""Download, process, and insert ISO 639-3 code tables into a database."""
import argparse
import io
import re
import sqlite3
import zipfile

import pandas as pd

from .utils import DOWNLOAD_DIR, download_file


CURRENT_DATE = "20180123"


def iso_639_3_url(current_date):
    """Get url to the zip file with ISO 639-3 Code Tables

    See `http://www-01.sil.org/iso639-3/download.asp`__.

    """
    return ("http://www-01.sil.org/iso639-3/"
            f"iso-639-3_Code_Tables_{current_date}.zip")


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
    url = iso_639_3_url(CURRENT_DATE)
    z = zipfile.ZipFile(download_file(url, DOWNLOAD_DIR))
    for tbl, filename in table2files(z):
        print(tbl, filename)
        with io.TextIOWrapper(z.open(filename, 'r')) as f:
            # there are some empty lines
            text = '\n'.join((line for line in f if line.strip() != ""))
            # important to adjust NA values otherwise Namibia is problematic
            dat = pd.read_csv(io.StringIO(text), delimiter='\t', na_values="",
                              keep_default_na=False)
            dat.to_sql(tbl, conn, if_exists='append', index=False)
    conn.commit()
    conn.close()


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="Path to SQLite database.")
    args = parser.parse_args()
    insert_data(args.db)


if __name__ == '__main__':
    main()

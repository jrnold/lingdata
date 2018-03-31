#!/usr/bin/env python3
"""Download Ethnologue code tables and save to a SQLite Database."""
import argparse
import io
import sqlite3
import zipfile

import pandas as pd

from .utils import download_file, DOWNLOAD_DIR

CURRENT_DATE = "20180221"
"""Current version of the Ethnologue code-point data."""


def ethnologue_url(current_date):
    """URL pattern for the Ethnologue data."""
    url = (f"https://www.ethnologue.com/codes/"
           f"Language_Code_Data_{current_date}.zip")
    return url


def insert_data(db):
    """Download data and insert into database ``db``."""
    conn = sqlite3.connect(db)
    url = ethnologue_url(CURRENT_DATE)
    z = zipfile.ZipFile(download_file(url, DOWNLOAD_DIR))
    tables = ("CountryCodes", "LanguageCodes", "LanguageIndex")
    for tbl in tables:
        with io.TextIOWrapper(z.open(f'{tbl}.tab', 'r')) as f:
            # important to adjust NA values otherwise Namibia is problematic
            dat = pd.read_csv(f, delimiter='\t', na_values="",
                              keep_default_na=False)
            if tbl == "LanguageIndex":
                dat = dat.dropna(axis = 0, how = 'all', subset = ('Name',))
            dat.to_sql(tbl, conn, if_exists='append', index=False)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="Path to SQLite database.")
    args = parser.parse_args()
    insert_data(args.db)


if __name__ == '__main__':
    main()

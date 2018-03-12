#!/usr/bin/env python3
"""Download Ethnologue code tables and save to a SQLite Database."""
import argparse
import io
import sqlite3
import zipfile

import pandas as pd
import requests

CURRENT_DATE = "20170221"

URL = f"https://www.ethnologue.com/codes/Language_Code_Data_{CURRENT_DATE}.zip"


def insert_data(db):
    """Download data and insert into database ``db``."""
    conn = sqlite3.connect(db)
    r = requests.get(URL, stream=True)
    z = zipfile.ZipFile(io.BytesIO(r.content), 'r')
    tables = ("CountryCodes", "LanguageCodes", "LanguageIndex")
    for tbl in tables:
        with io.TextIOWrapper(z.open(f'{tbl}.tab', 'r')) as f:
            # important to adjust NA values otherwise Namibia is problematic
            dat = pd.read_csv(f, delimiter='\t', na_values="",
                              keep_default_na=False)
            dat.to_sql(tbl, conn, if_exists='append', index=False)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_arguments("db", help="Path to SQLite database.")
    args = parser.parse_arguments()
    insert_data(args.db)


if __name__ == '__main__':
    main()

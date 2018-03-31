#!/usr/bin/env python3
"""Download Ethnologue code tables and save to a SQLite Database."""
import argparse
import io
import os
import os.path
import sqlite3
import zipfile

import pandas as pd
import requests

CURRENT_DATE = "20170221"

URL = f"https://www.ethnologue.com/codes/Language_Code_Data_{CURRENT_DATE}.zip"

DOWNLOAD_DIR = "downloads"

def download_file(url, dst):
    """Download and save file if it does not exists."""
    os.makedirs(dst, exist_ok=True)
    outfile = os.path.join(dst, os.path.basename(url)))
    if not os.path.exists(outfile):
      r = requests.get(url, stream=True)
      with open(outfile, 'wb') as f:
        f.write(r.content)
    return outfile

def insert_data(db):
    """Download data and insert into database ``db``."""
    conn = sqlite3.connect(db)
    z = zipfile.ZipFile(download_file(URL, DOWNLOAD_DIR))
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
    parser.add_argument("db", help="Path to SQLite database.")
    args = parser.parse_args()
    insert_data(args.db)


if __name__ == '__main__':
    main()

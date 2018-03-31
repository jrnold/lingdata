"""Utility functions used in by the other modules."""
import os.path

import requests


DOWNLOAD_DIR = "downloads"
"""Default name of the directory to cach download files."""


def set_sql_opts(con):
    """Set SQL options to speed up loading data."""
    con.isolation_level = "DEFERRED"
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA journal_mode=MEMORY")


def unset_sql_opts(con):
    """Unset SQL options that sped up loading data."""
    con.execute("PRAGMA synchronous=ON")
    con.execute("PRAGMA journal_mode=WAL")


def download_file(url, dst):
    """Download ``url`` to ``dst`` if ``dst`` does not exist."""
    os.makedirs(dst, exist_ok=True)
    downloaded_file = os.path.join(dst, os.path.basename(url))
    if not os.path.exists(downloaded_file):
        r = requests.get(url, stream=True)
        with open(downloaded_file, 'wb') as f:
            f.write(r.content)
    return downloaded_file

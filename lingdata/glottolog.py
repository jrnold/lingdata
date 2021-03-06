#!/usr/bin/env python3
# coding: utf-8
"""Download Glottolog data, process it, and save it to a SQLite database."""
import argparse
import functools
import io
import itertools
import re
import sqlite3
import zipfile

import numpy as np
import pandas as pd
import requests
import newick
from geopy.distance import great_circle

from .utils import set_sql_opts, unset_sql_opts, download_file, DOWNLOAD_DIR

URLS = {
    "lang_geo":
    ("https://cdstar.shh.mpg.de/bitstreams/EAEA0-F088-DE0E-0712-0/"
     "languages_and_dialects_geo.csv"),
    "languoids":
    ("https://cdstar.shh.mpg.de/bitstreams/EAEA0-F088-DE0E-0712-0/"
     "glottolog_languoid.csv.zip"),
    "resourcemap":
    "http://glottolog.org/resourcemap.json?rsc=language",
    "glottolog-newick":
    ("https://cdstar.shh.mpg.de/bitstreams/EAEA0-F088-DE0E-0712-0/"
     "tree_glottolog_newick.txt")
}


def geomean(long, lat, w=None):
    """Mean location for spherical coordinates.

    Parameters
    -----------
    long: :py:class:`~numpy.array`
        Longitude
    lat: :py:class:`~numpy.array`
        Latitude
    w: :py:class:`~numpy.array`
        Weights

    Returns
    ------------
    (longitude, latitude): tuple of :py:class:`~numpy.array`
        The average latitude and longitude coordinates

    Based on the function goemean in the R package geosphere.

    """
    long = np.array(long)
    lat = np.array(lat)
    if not w:
        w = np.ones(len(long))
    w = w / sum(w)
    long = (long + 180) * np.pi / 180
    long = np.arctan2(np.mean(np.sin(long) * w), np.mean(np.cos(long) * w))
    long = long % (2 * np.pi) - np.pi
    lat = lat * np.pi / 180
    lat = np.arctan2(np.mean(np.sin(lat) * w), np.mean(np.cos(lat) * w))
    return (long * 180 / np.pi, lat * 180 / np.pi)


def set2str(x):
    """Convert list or set ``x`` to a space separated string."""
    return ' '.join(x) if len(x) else None


def table_colnames(conn, table):
    """Get the colnames of SQLite table ``table`` from connection ``conn``."""
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table}")
    r = c.fetchone()
    return [x[0] for x in r.description]


def get_languoids():
    """Download Glottolog Languoids Data."""
    z = zipfile.ZipFile(download_file(URLS['languoids'], DOWNLOAD_DIR))
    with io.TextIOWrapper(z.open('languoid.csv', 'r')) as f:
        languoids = pd.read_csv(f)
    languoids = languoids.loc[:, (
        'id', 'name', 'iso639P3code', 'family_id', 'parent_id', 'latitude',
        'longitude', 'level', 'status', 'bookkeeping', 'child_family_count',
        'child_language_count', 'child_dialect_count', 'country_ids')]
    languoids.rename(
        index=str,
        columns={"id": "glottocode",
                 "iso639P3code": "iso_639_3"},
        inplace=True)
    languoids.set_index('glottocode', inplace=True)
    return languoids


def get_lang_geo():
    """Download geographic information for Glottolog languoids."""
    out = pd.read_csv(URLS['lang_geo'], index_col="glottocode")
    return out.loc[:, ('macroarea', )]


def get_resourcemap():
    """Download the Glottolog reourcemap data."""
    return requests.get(URLS['resourcemap']).json()


def is_wals_lang_id(x):
    """Check if identifier ``x`` is a WALS language."""
    return x['type'] == "wals" and re.match("[a-z]{2,3}$", x['identifier'])


def is_iso_lang_id(x):
    """Check if identifier ``x`` is a ISO 639-3 language."""
    return x['type'] == "iso639-3" and re.match("[a-z]{3}$", x['identifier'])


def glottolog_tree():
    """Download and parse the Glottolog language tree."""
    def parse_node(x):
        """Parse each node in the Newick tree."""
        node_pattern = """^'?
            (?P<name> .* ) [ ]
            \[ (?P<glottocode> [a-z0-9]{8} ) \]
            (?: \[ (?P<iso_639_3> [a-z]{3} ) \] ) ?
            (?P<language> -l- ) ?
        '?$"""
        m = re.match(node_pattern, x, re.X)
        if m is not None:
            out = m.groupdict()
            out['language'] = out['language'] is not None
            return out

    def walk_tree(x):
        """Walk the language tree."""
        node = parse_node(x.name)
        node['children'] = [walk_tree(n) for n in x.descendants]
        return node

    url = URLS['glottolog-newick']
    r = requests.get(url)
    tree = newick.loads(r.text)
    return [walk_tree(branch) for branch in tree]


def walk_tree(x, depth=1, ancestors=[], family=None, newdata={}):
    """Depth first traversal of the the Glottolog tree.

    While traversing the tree this fills in lists of ancestors and descendants.
    """
    glottocode = x["glottocode"]
    data = newdata[glottocode]

    if depth == 1:
        data['family'] = glottocode
    else:
        data['family'] = family
    f = functools.partial(
        walk_tree,
        depth=depth + 1,
        family=data['family'],
        ancestors=ancestors + [glottocode],
        newdata=newdata)
    children_data = [f(child) for child in x["children"]]
    for c in children_data:
        data['wals_codes'].update(c['wals_codes'])
        data['iso_639_3'].update(c['iso_639_3'])
        data['macroarea'].update(c['macroarea'])
        try:
            data['country_ids'].update(c['country_ids'])
        except KeyError as exc:
            print(data)
            print(c)
            raise exc

    # Bump descendants back one level
    data['descendants'] = {}
    for c in children_data:
        data['descendants'][c['glottocode']] = -1
        for k, v in c['descendants'].items():
            data['descendants'][k] = v - 1

    # if one is missing, both are
    if not data['latitude']:
        child_lat = [
            c['latitude'] for c in children_data
            if c['latitude'] and not pd.isnull(c['latitude'])
        ]
        child_long = [
            c['longitude'] for c in children_data
            if c['longitude'] and not pd.isnull(c['longitude'])
        ]
        if len(child_long):
            data['longitude'], data['latitude'] = geomean(
                np.array(child_long), np.array(child_lat))
        else:
            data['longitude'] = data['latitude'] = None

    if len(data['descendants']):
        subtree_depth = -1 * min(data['descendants'].values())
    else:
        subtree_depth = 0

    parent = ancestors[-1] if len(ancestors) else None

    data.update({
        'parent': parent,
        'ancestors': ancestors,
        'depth': depth,
        'family': family,
        'subtree_depth': subtree_depth,
    })
    return {
        'glottocode': data['glottocode'],
        'descendants': data['descendants'],
        'iso_639_3': data['iso_639_3'],
        'wals_codes': data['wals_codes'],
        'country_ids': data['country_ids'],
        'macroarea': data['macroarea'],
        'latitude': data['latitude'],
        'longitude': data['longitude'],
    }


def topdown_fill(x, newdata={}):
    """Fill in data from parents."""
    data = newdata[x['glottocode']]
    if data['parent']:
        parent = newdata[data['parent']]
        for i in ('wals_codes', 'iso_639_3', 'macroarea', 'country_ids'):
            if not len(data[i]):
                data[i].update(parent[i])
        for i in ('longitude', 'latitude'):
            if not data[i]:
                data[i] = parent[i]
    for child in x['children']:
        topdown_fill(child, newdata)


def create_langdata(glottolog_tree):
    """Create Glottolog language data."""
    # Get external data
    resourcemap = get_resourcemap()
    languoids = get_languoids()
    lang_geo = get_lang_geo()
    languoids = languoids.merge(
        lang_geo, how='left', left_index=True, right_index=True)
    # Dictionaries for Glottocode -> ISO, WALS code lookups
    glotto2wals = {}
    for x in resourcemap['resources']:
        for id_ in x['identifiers']:
            if is_wals_lang_id(id_):
                glotto2wals[x["id"]] = id_["identifier"]

    # It'll be much easier to work with dict of dicts than a pandas
    # dataframe when walking the tree
    newdata = dict((x['glottocode'], x)
                   for x in languoids.reset_index().to_dict('records'))
    for k, v in newdata.items():
        for j in ('longitude', 'latitude'):
            if pd.isnull(v[j]):
                v[j] = None
        for j in ('macroarea', 'iso_639_3'):
            if pd.isnull(v[j]):
                v[j] = set()
            else:
                v[j] = set((v[j], ))
        if pd.isna(v['country_ids']):
            v['country_ids'] = set()
        else:
            v['country_ids'] = set(v['country_ids'].split(' '))
        try:
            v['wals_codes'] = set((glotto2wals[k], ))
        except KeyError:
            v['wals_codes'] = set()

    # Fill in data bottom-up: children -> parents
    for subtree in glottolog_tree:
        walk_tree(subtree, newdata=newdata)

    # Fill in data top-down: parents -> children
    for subtree in glottolog_tree:
        topdown_fill(subtree, newdata=newdata)
    return newdata


def create_distmat(newdata):
    """Create the language distance matrix."""
    langsdata = [
        x for x in newdata.values()
        if x['level'] in ("language", "dialect") and "family" in x
    ]
    for lang1, lang2 in itertools.product(langsdata, langsdata):
        if (lang1["glottocode"] != lang2["glottocode"]
                and lang1["family"] == lang2["family"]):
            shared = len(set(lang1['ancestors']) & set(lang2['ancestors']))
            geo = great_circle((lang1['latitude'], lang2['longitude']),
                               (lang2['latitude'], lang2['longitude']))
            yield (lang1["glottocode"], lang2["glottocode"], shared, geo.m)


def insert_languoids(conn, langdata):
    """Insert language data into the database."""
    colnames = ('glottocode', 'name', 'latitude', 'longitude', 'level',
                'status', 'bookkeeping', 'parent_id', 'family_id',
                'child_family_count', 'child_language_count',
                'child_dialect_count', 'depth', 'subtree_depth')

    def iterrows(langdata):
        """Iterate over each row in the table."""
        for lang in langdata:
            row = (
                lang['glottocode'],
                lang['name'],
                lang['latitude'],
                lang['longitude'],
                lang['level'],
                lang['status'],
                lang['bookkeeping'],
                lang['parent_id'],
                lang['family_id'],
                lang['child_family_count'],
                lang['child_language_count'],
                lang['child_dialect_count'],
                # bookkeeping entries aren't in the hierarchy
                lang.get('depth'),
                lang.get('subtree_depth'))
            yield row

    c = conn.cursor()
    sql = (
        "INSERT INTO languoids VALUES (%s)" % ', '.join(['?'] * len(colnames)))
    c.executemany(sql, iterrows(langdata))
    conn.commit()


def insert_paths(conn, langdata):
    """Insert data into the paths table."""
    def iterlangs(langdata):
        # Get ancestors
        for lang in langdata:
            # Bookkeeping entries dont' have tree info
            try:
                for i, node in enumerate(reversed(lang['ancestors'])):
                    yield (lang['glottocode'], node, i + 1)
            except KeyError:
                pass
            # Get descendants
            try:
                for k, v in lang['descendants'].items():
                    yield (lang['glottocode'], k, v)
            except KeyError:
                pass

    c = conn.cursor()
    sql = "INSERT INTO paths VALUES (?, ?, ?)"
    c.executemany(sql, iterlangs(langdata))
    conn.commit()


def insert_distances(conn, distances):
    """Insert Glottolog language distances."""
    c = conn.cursor()
    sql = "INSERT INTO distances VALUES (?, ?, ?, ?)"
    c.executemany(sql, distances)
    conn.commit()


def insert_iso_codes(conn, langdata):
    """Insert Glottlog-ISO 369-3 codes into the database."""
    def iterlangs(langdata):
        for lang in langdata:
            for iso_code in lang['iso_639_3']:
                yield (lang['glottocode'], iso_code)

    c = conn.cursor()
    sql = "INSERT INTO iso_codes VALUES (?, ?)"
    c.executemany(sql, iterlangs(langdata))
    conn.commit()


def insert_wals_codes(conn, langdata):
    """Insert Glottlog-WALS mappings into the database."""
    def iterlangs(langdata):
        for lang in langdata:
            for wals_code in lang['wals_codes']:
                yield (lang['glottocode'], wals_code)

    c = conn.cursor()
    sql = "INSERT INTO wals_codes VALUES (?, ?)"
    c.executemany(sql, iterlangs(langdata))
    conn.commit()


def insert_macroareas(conn, langdata):
    """Insert data into the macroareas table of the Glottolog database."""
    def iterlangs(langdata):
        for lang in langdata:
            for macroarea in lang['macroarea']:
                yield (lang['glottocode'], macroarea)

    c = conn.cursor()
    sql = "INSERT INTO macroareas VALUES (?, ?)"
    c.executemany(sql, iterlangs(langdata))
    conn.commit()


def insert_countries(conn, langdata):
    """Insert countries into the Glottolog database."""
    def iterlangs(langdata):
        for lang in langdata:
            for country in lang['country_ids']:
                yield (lang['glottocode'], country)

    c = conn.cursor()
    sql = "INSERT INTO countries VALUES (?, ?)"
    c.executemany(sql, iterlangs(langdata))
    conn.commit()


def run(outfile):
    """Insert data in a SQLite database."""
    langdata = create_langdata(glottolog_tree())
    distances = create_distmat(langdata)
    # Initialize database and create tables
    conn = sqlite3.connect(outfile)
    set_sql_opts(conn)
    insert_languoids(conn, langdata.values())
    insert_paths(conn, langdata.values())
    insert_distances(conn, distances)
    insert_wals_codes(conn, langdata.values())
    insert_iso_codes(conn, langdata.values())
    insert_macroareas(conn, langdata.values())
    insert_countries(conn, langdata.values())
    unset_sql_opts(conn)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="Path to SQLite database.")
    args = parser.parse_args()
    run(args.db)


if __name__ == '__main__':
    main()

# coding: utf-8
import csv
import io
import json
import zipfile
import functools
from itertools import chain
import re

import yaml
import newick
import numpy as np
import pandas as pd
import requests
import geopy
from geopy.distance import vincenty

INPUTS = {'tree-glottolog': 'glottolog-tree.json'}

URLS = {
    'lang_geo': 'http://glottolog.org/static/download/languages-and-dialects-geo.csv',
    'languoids': 'http://glottolog.org/static/download/glottolog-languoid.csv.zip',
    'resourcemap': 'http://glottolog.org/resourcemap.json?rsc=language'
}

"""
CREATE TABLE languages (
    glottocode CHAR(8) NOT NULL PRIMARY KEY,
    iso_639_3 CHAR(3),
    wals_codes CHAR(3),
    macroarea TEXT,

    latitude REAL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL CHECK (longitude BETWEEN -180 AND 180),

    level TEXT CHECK (level IN ('family', 'language', 'dialect')),
    status TEXT,
    bookkeeping BOOLEAN,

    parent CHAR(8),
    depth INT CHECK (depth > 0),
    subtree_depth INT (subtree_depth >= 0),
    ancestors TEXT,  -- should go in diff table
    children TEXT, -- should go in diff table
    descendants TEXT -- should go in diff table

)

CREATE TABLE distances (
    glottocode_1 CHAR(8),
    glottocode_2 CHAR(8),
    geo REAL CHECK (geo >= 0),
    shared INT CHECK (shared >= 0),
    PRIMARY KEY (glottocode_1, glottocode_2),
    FOREIGN KEY (glottocode_1) REFERENCES languages (glottocode),
    FOREIGN KEY (glottocode_2) REFERENCES languages (glottocode)
)
"""


def get_languoids():
    """ Download Glottolog Languoids Data """
    r = requests.get(URLS['languoids'])
    z = zipfile.ZipFile(io.BytesIO(r.content), 'r')
    with io.TextIOWrapper(z.open('languoid.csv', 'r')) as f:
        languoids = pd.read_csv(f)
    languoids = languoids.loc[:, ('id', 'hid', 'macroarea', 'latitude',
                                      'longitude', 'level',
                                       'status', 'bookkeeping')]
    languoids.rename(index=str, columns={"id": "glottocode",
                                             "hid": "iso_639_3"}, inplace=True)
    languoids.set_index('glottocode', inplace=True)
    return languoids


def get_lang_geo():
    return pd.read_csv(URLS['lang_geo'], index_col="glottocode")


def get_resourcemap():
    return requests.get(URLS['resourcemap']).json()

def is_wals_lang_id(x):
    return x['type'] == "wals" and re.match("[a-z]{2,3}$", x['identifier'])

def is_iso_lang_id(x):
    return x['type'] == "iso639-3" and re.match("[a-z]{3}$", x['identifier'])


def walk_tree(x, depth=1, ancestors=[], family=None, newdata = {}):
    """ Depth first search through tree

    Fills in ids, gets list of ancestors and descendants
    """
    glottocode = x["glottocode"]
    data = newdata[glottocode]
    if depth == 1:
        data['family'] = glottocode
    else:
        data['family'] = family
    f = functools.partial(walk_tree, depth=depth + 1,
                          family=data['family'],
                          ancestors = ancestors + [glottocode],
                          newdata = newdata)
    children_data = [f(child) for child in x["children"]]
    data['descendants'] = set()
    for c in children_data:
        data['descendants'].update(c['glottocodes'])
        data['wals_codes'].update(c['wals_codes'])
        data['iso_639_3'].update(c['iso_639_3'])
        data['macroarea'].update(c['macroarea'])

    # this isn't the right way to average over geographic points. Need to find the
    # python equivalent of geosphere
    # This is problematic and doesn't handle the 180 question
    if not data['latitude']:
        child_lat = [c['latitude'] for c in children_data
                     if c['latitude'] and not pd.isnull(c['latitude'])]
        data['latitude'] = np.mean(child_lat) if len(child_lat) else None
    if not data['longitude']:
        child_long = [c['longitude'] for c in children_data
                      if c['longitude'] and not pd.isnull(c['longitude'])]
        data['longitude'] = np.mean(child_long) if len(child_long) else None
    if len(children_data):
        subtree_depth = max(c['subtree_depth'] for  c in children_data) + 1
    else:
        subtree_depth = 0

    #geo_lookup[[glottocode]]
    data.update({
        'parent': ancestors[-1] if len(ancestors) else None,
        'children': [child['glottocode'] for child in x["children"]],
        'ancestors': ancestors,
        'depth': depth,
        'subtree_depth': subtree_depth,
        'family': family
    })

    return {
        'glottocodes': set([glottocode] + list(data['descendants'])),
        'iso_639_3': data['iso_639_3'],
        'wals_codes': data['wals_codes'],
        'macroarea': data['macroarea'],
        'latitude': data['latitude'],
        'longitude': data['longitude'],
        'subtree_depth': subtree_depth,
        'family': data['family']
    }


def topdown_fill(x, newdata = {}):
    """ Fill in data from parents """
    data = newdata[x['glottocode']]
    if data['parent']:
        parent = newdata[data['parent']]
        for i in ('wals_codes', 'iso_639_3', 'macroarea'):
            if not len(data[i]):
                data[i].update(parent[i])
        for i in ('longitude', 'latitude'):
            if not data[i]:
                data[i] = parent[i]
    for child in x['children']:
        topdown_fill(child, newdata)

def clean_row(row):
    for k, v in row.items():
        if isinstance(v, set):
            row[k] = list(v)

def create_langdata():
    # Get external data
    resourcemap = get_resourcemap()
    languoids = get_languoids()
    lang_geo = get_lang_geo()
    # Dictionaries for Glottocode -> ISO, WALS code lookups
    glotto2wals = {}
    glotto2iso = {}
    for x in resourcemap['resources']:
        for id_ in x['identifiers']:
            if is_iso_lang_id(id_):
                glotto2iso[x["id"]] = id_['identifier']
            elif is_wals_lang_id(id_):
                glotto2wals[x["id"]] = id_["identifier"]

    newdata = dict((x['glottocode'], x) for x
                   in languoids.reset_index().to_dict('records'))
    for k, v in newdata.items():
        for j in ('longitude', 'latitude'):
            if pd.isnull(v[j]):
                v[j] = None
        for j in ('macroarea', 'iso_639_3'):
            if pd.isnull(v[j]):
                v[j] = set()
            else:
                v[j] = set((v[j],))
        try:
            v['wals_codes'] = {glotto2wals[k]}
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
    language_dists = []
    langsdata = [x for x in newdata.values() if x['level']
                 in ("language", "dialect") and "family" in x]
    for lang1, lang2 in itertools.product(langsdata, langsdata):
        if (lang1["glottocode"] != lang2["glottocode"] and
                lang1["family"] == lang2["family"]):
            shared = len(set(lang1['ancestors']) & set(lang2['ancestors']))
            geo = vincenty((lang1['latitude'], lang2['longitude']),
                           (lang2['latitude'], lang2['longitude']))
            language_dists.append({'glottocode_from': lang1["glottocode"],
                                   'glottocode_to': lang2["glottocode"],
                                   'shared': shared,
                                   'geo': geo
                                  })
    return language_dists

def run(glottolog_tree):
    langdata = create_langdata()
    dists = create_distmat(langdata)

    newdata = [clean_row(row) for row in newdata.values()]
    with open('foo.json', 'w') as f:
        json.dump(newdata, f, indent = 2)

def main():
    with open(INPUTS['tree-glottolog'], 'r') as f:
        glottolog_tree = json.load(f)
    run(glottolog_tree)

if __name__ == '__main__':
    main()

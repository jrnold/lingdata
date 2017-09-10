import collections
import io
import itertools
import json
import os
import re
import sqlite3
import zipfile
from collections import defaultdict

import Levenshtein
import pandas as pd
import requests

URL = "http://asjp.clld.org/static/download/asjp-dataset.tab.zip"


def create_tables(conn):
    c = conn.cursor()
    c.execute("""
    CREATE TABLE meanings (
        meaning TEXT PRIMARY KEY,
        num INTEGER UNIQUE,
        in_forty BOOLEAN NOT NULL
    )""")
    c.execute("""
    CREATE TABLE languages (
        language TEXT PRIMARY KEY,
        wls_fam TEXT NOT NULL,
        wls_gen TEXT NOT NULL,
        e TEXT,
        hh TEXT,
        lat NUMERIC CHECK (lat BETWEEN -90 AND 90),
        lon NUMERIC CHECK (lon BETWEEN -180 AND 180),
        pop INTEGER CHECK (pop >= 0),
        wcode CHAR(3),
        iso CHAR(3)
    )""")
    c.execute("""
    CREATE TABLE wordlists (
        language TEXT NOT NULL,
        meaning TEXT NOT NULL,
        word TEXT NOT NULL,
        synonym_num INTEGER CHECK (synonym_num >= 1),
        loanword BOOLEAN NOT NULL,
        PRIMARY KEY (language, meaning, word),
        FOREIGN KEY (language) REFERENCES languages (language),
        FOREIGN KEY (meaning) REFERENCES meanings (meaning)
    )""")
    c.execute("""
    CREATE TABLE distances (
        language_1 TEXT NOT NULL,
        language_2 TEXT NOT NULL,
        ldn NUMERIC NOT NULL CHECK (ldn BETWEEN 0 AND 1),
        ldnd NUMERIC NOT NULL CHECK (ldnd >= 0),
        common_words INTEGER NOT NULL CHECK (common_words >= 1),
        PRIMARY KEY (language_1, language_2),
        FOREIGN KEY (language_2) REFERENCES languages (language),
        FOREIGN KEY (language_1) REFERENCES languages (language)
    )""")
    conn.commit()


def insert_meanings(conn):
    with open('ASJP_meanings.json', 'r') as f:
        meanings = json.load(f)
    c = conn.cursor()
    for meaning, v in meanings.items():
        c.execute("INSERT INTO meanings VALUES (?, ?, ?)",
                  (meaning, v['id'], v['in_forty']))
    conn.commit()

# Iterate over all pairs of languages; the comparison removes duplicate
# and self-comparisons.
# - Calculate LD, LDN, and LDND for all pairs
# - use Futures for multiprocessing
# - save to database


def lexidists(words1, words2, min_words=2):
    ldn_sum = 0.
    ldnd_denom = 0.
    common_words = set(words1.keys()) & set(words2.keys())
    M = len(common_words)
    if (M > min_words):
        for meaning1, meaning2 in itertools.product(common_words,
                                                    common_words):
            # ignore duplicated non-equal meanings
            if meaning1 > meaning2:
                continue
            d = 0
            wcomp = list(itertools.product(words1[meaning1], words2[meaning2]))
            for w1, w2 in wcomp:
                d += Levenshtein.distance(w1, w2) / max(len(w1), len(w2))
            d /= len(wcomp)
            if meaning1 == meaning2:
                ldn_sum += d
            else:
                ldnd_denom += d
        return {'ldn': ldn_sum / M,
                # The  (M * (M - 1) / 2) / M = (M - 1) / 2
                'ldnd': 0.5 * (M - 1) * ldn_sum / ldnd_denom,
                'M': M}


def compare_langs(lang1, lang2):
    # each language is a name (str), wordlist (dict) tuple
    d = lexidists(lang1[1], lang2[1])
    # some pairs have NO overlap
    if d:
        return (lang1[0], lang2[0], d['ldn'], d['ldnd'], d['M'])


def run(dbname):
    r = requests.get(URL, stream=True)
    asjp_dataset = zipfile.ZipFile(io.BytesIO(r.content))

    try:
        os.remove(dbname)
    except FileNotFoundError:
        pass

    conn = sqlite3.connect(dbname)
    create_tables(conn)
    insert_meanings(conn)

    c = conn.cursor()
    with asjp_dataset.open('dataset.tab', 'r') as f:
        data = pd.read_csv(f, delimiter='\t', encoding='CP1252')
    data.rename(index=str, columns={'names': 'language'}, inplace=True)
    lang_variables = ('language', 'wls_fam', 'wls_gen', 'e', 'hh',
                      'lat', 'lon', 'pop', 'wcode', 'iso')
    # use list comprehension instead of set diff in order to keep the order
    word_variables = [c for c in data.columns if c not in lang_variables]

    data.loc[:, lang_variables].to_sql('languages', conn,
                                       index=False, if_exists='append')

    wordlists = data.loc[:, ['language'] + word_variables].\
        melt(id_vars='language', var_name='meaning', value_name='word')
    wordlists = wordlists.dropna(axis=0)

    for row in wordlists.itertuples(False):
        if pd.notnull(row.word) and len(row.word) > 0:
            # there are some duplicate words; set removes duplicates
            words = set(re.split(r',\s*', row.word))
            for i, w in enumerate(words):
                if w.startswith('%'):
                    loanword = True
                    w = w[1:]
                else:
                    loanword = False
                if w == '':
                    continue
                c.execute("INSERT INTO wordlists VALUES (?, ?, ?, ?, ?)",
                          (row.language, row.meaning, w, i + 1, loanword))
    conn.commit()

    langpairs = set(c.execute("""
        SELECT a.language as language_1,
        b.language as language_2
        FROM languages as a
        INNER JOIN languages as b
        ON a.wls_fam = b.wls_fam
        WHERE a.language < b.language
    """).fetchall())

    res = c.execute("""
        SELECT language, wordlists.meaning, word
        FROM wordlists
        INNER JOIN meanings
        ON meanings.meaning = wordlists.meaning
        WHERE in_forty AND NOT loanword
    """)

    wordlist_dict = defaultdict(lambda: collections.defaultdict(list))

    for language, meaning, word in res:
        wordlist_dict[language][meaning].append(word)
    wordlist_dict = dict(wordlist_dict)

    wordlist_iter = ((x, y) for x, y
                     in itertools.product(wordlist_dict.items(),
                                          wordlist_dict.items())
                     if (x[0], y[0]) in langpairs)
    update_intvl = 10000
    results = (compare_langs(*x) for x in wordlist_iter)
    batch = []
    for i, res in enumerate(results):
        if res:
            batch.append(res)
        if ((i + 1) % update_intvl == 0):
            c.executemany("INSERT INTO distances VALUES (?, ?, ?, ?, ?)",
                          batch)
            batch = []
            print("Processed %d" % (i + 1))
            conn.commit()
    conn.commit()


def main():
    dbname = "ASJP.db"
    run(dbname)


if __name__ == '__main__':
    main()

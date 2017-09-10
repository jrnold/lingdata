"""
Download the Newick tree form of the Glottolog hierachy and save to JSON
"""
import json
import re
import argparse
import sys

import newick
import requests

URLS = {'glottolog-newick':
        'http://glottolog.org/static/download/tree-glottolog-newick.txt'}


def parse_node(x):
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
    node = parse_node(x.name)
    node['children'] = [walk_tree(n) for n in x.descendants]
    return node


def run(url, dst):
    r = requests.get(url)
    tree = newick.loads(r.text)
    glottolog_tree = [walk_tree(branch) for branch in tree]
    json.dump(glottolog_tree, dst)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)
    args = parser.parse_args()
    run(URLS['glottolog-newick'], args.outfile)


if __name__ == "__main__":
    main()

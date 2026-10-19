#!/usr/bin/env python3
"""Resolve preserved aliases without loading or executing the modules."""
import argparse
import json
from pathlib import Path
import re
import unicodedata

def normalize(value):
    text = unicodedata.normalize('NFKD', value.casefold())
    return ' '.join(''.join(c for c in text if not unicodedata.combining(c)).split())

def select(query, records):
    query = normalize(query)
    exact = [r for r in records if query in [normalize(a) for a in r['aliases']]]
    if exact:
        return exact
    occurrences = []
    for record in records:
        for alias in record['aliases']:
            phrase = normalize(alias)
            pattern = re.compile(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)')
            occurrences.extend((record, phrase, match.start(), match.end()) for match in pattern.finditer(query))

    selected = []
    for record in records:
        record_matches = [item for item in occurrences if item[0] is record]
        if any(not any(
            other[1] != phrase and other[2] <= start and end <= other[3]
            for other in occurrences
        ) for _, phrase, start, end in record_matches):
            selected.append(record)
    return selected

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query', required=True)
    args = parser.parse_args()
    root = Path(__file__).absolute().parent.parent
    data = json.loads((root / 'references/aliases.json').read_text())
    matches = select(args.query, data['modules'])
    print(json.dumps([{'name': r['name'], 'module': str(root / r['module'])} for r in matches], ensure_ascii=False))
    return 0 if matches else 2

if __name__ == '__main__':
    raise SystemExit(main())

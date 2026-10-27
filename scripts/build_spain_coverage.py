"""Export only confirmed locality/province coverage, never archive records or notes.

Usage: python3 scripts/build_spain_coverage.py INPUT_HTML OUTPUT_JSON
The input stays outside the public repository. Browser-only availability edits
must first be exported and incorporated in the internal explorer.
"""
import argparse
import json
import math
import unicodedata
from collections import defaultdict
from pathlib import Path


def normalise(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold())
                   if unicodedata.category(c) != 'Mn').strip()


def export(source):
    data = json.JSONDecoder().raw_decode(source.split('const D = ', 1)[1])[0]
    rules = {('p', r.get('clave')) if r.get('nivel') == 'parroquia'
             else ('d', r.get('diocesis')): r for r in data.get('availability', [])}
    places = defaultdict(list)
    for place in data['places']:
        places[normalise(place[0])].append(place)
    result = set()
    for row in data['rows']:
        rule = rules.get(('p', row[0]), rules.get(('d', data['dioceses'][row[2]]), rules.get(('d', '*'), {})))
        # A limited or provisional rule must never become unconditional coverage.
        if normalise(rule.get('disponible', '')) != 'si' or any(rule.get(k) for k in ('desde', 'hasta', 'tipos')):
            continue
        if row[3] is None or row[4] is None:
            continue
        matches = []
        for place in places[normalise(row[16] or row[1])]:
            distance = math.hypot((place[1]-row[3])*111,
                                  (place[2]-row[4])*111*math.cos(math.radians(row[3])))
            if distance <= 3:
                matches.append(place)
        # Exact name plus nearby coordinates, with no ambiguous province inference.
        if len(matches) != 1:
            continue
        place = matches[0]
        result.add((data['provinces'][place[3]], place[0]))
    return {'version': 1, 'localities': [
        {'province': province, 'locality': locality, 'status': 'available'}
        for province, locality in sorted(result)]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = export(args.input.read_text(encoding='utf-8'))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"Exported {len(result['localities'])} public locality/province pairs.")

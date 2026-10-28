"""Export only confirmed locality/province coverage, never archive records or notes.

Each locality is "available" (an unconditional service rule) or "unavailable" (a rule saying no), with its diocese
("area", the name of its map area). Conditional rules are left out: those places need an individual assessment.

Usage: python3 scripts/build_spain_coverage.py INPUT_HTML OUTPUT_JSON
The input stays outside the public repository. Browser-only availability edits
must first be exported and incorporated in the internal explorer.
"""
import argparse
import json
import math
import unicodedata
from collections import Counter, defaultdict
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
    fixes = {f.get('clave'): f for f in data.get('fixes', [])}
    result = defaultdict(lambda: {'available': Counter(), 'unavailable': Counter()})
    for row in data['rows']:
        diocese = data['dioceses'][row[2]]
        rule = rules.get(('p', row[0]), rules.get(('d', diocese), rules.get(('d', '*'), {})))
        # A limited or provisional rule must never become unconditional coverage.
        state = normalise(rule.get('disponible', ''))
        if state == 'si' and not any(rule.get(k) for k in ('desde', 'hasta', 'tipos')):
            status = 'available'
        elif state == 'no':
            status = 'unavailable'
        else:
            continue
        # The explorer's own corrections: a hidden parish is dropped, a moved one is matched where it now lies.
        fix = fixes.get(row[0], {})
        if fix.get('accion') == 'ocultar':
            continue
        if fix.get('lat') and fix.get('lon'):
            row = row[:3] + [float(fix['lat']), float(fix['lon'])] + row[5:]
        if row[3] is None or row[4] is None:
            continue
        matches = []
        for place in places[normalise(row[16] or row[1])]:
            distance = math.hypot((place[1]-row[3])*111,
                                  (place[2]-row[4])*111*math.cos(math.radians(row[3])))
            if distance <= 3:
                matches.append(place)
        # Exact name plus nearby coordinates, with no ambiguous province inference.
        if len(matches) != 1 or not data['provinces'][matches[0][3]]:
            continue
        place = matches[0]
        result[(data['provinces'][place[3]], place[0])][status][diocese] += 1
    localities = []
    for (province, locality), found in sorted(result.items()):
        # A place with any confirmed route is available; its area is the diocese of most of those parishes.
        status = 'available' if found['available'] else 'unavailable'
        localities.append({'province': province, 'locality': locality, 'status': status,
                           'area': found[status].most_common(1)[0][0]})
    return {'version': 2, 'localities': localities}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = export(args.input.read_text(encoding='utf-8'))
    rows = ',\n'.join(json.dumps(row, ensure_ascii=False) for row in result['localities'])
    args.output.write_text(f'{{"version": {result["version"]}, "localities": [\n{rows}\n]}}\n', encoding='utf-8')
    print(f"Exported {len(result['localities'])} public locality/province pairs.")

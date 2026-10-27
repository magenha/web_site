"""Export the public coverage map: area names, scope and outlines only, never parishes or archive records.

Usage: python3 scripts/build_spain_coverage_map.py INPUT_GEOJSON OUTPUT_JSON [--hide NAME ...]
The input is the internal explorer's Output/cobertura/cobertura.geojson (built by cobertura.py), kept
outside the public repository. --hide leaves an area out of the public map.
"""
import argparse
import json
from pathlib import Path

SOURCE = 'Municipal boundaries: es-atlas 0.6.0, CC BY 4.0 © Instituto Geográfico Nacional'
STATUS = {'si': 'available', 'con reservas': 'limited'}


def point(p):
    return [round(float(p[0]), 3), round(float(p[1]), 3)]


def ring(points):
    out = []
    for p in map(point, points):
        if not out or p != out[-1]:
            out.append(p)
    return out if len(out) >= 4 else None


def export(source, hide=()):
    areas = []
    for feature in source['features']:
        props = feature['properties']
        status = STATUS.get(str(props.get('servicio', '')).strip().lower())
        if not status or props['nombre'] in hide:
            continue
        polygons = []
        for polygon in feature['geometry']['coordinates']:
            rings = [r for r in map(ring, polygon) if r]
            if rings:
                polygons.append(rings)
        scope = [{'province': str(p['provincia']), 'whole': bool(p['toda']), 'municipalities': int(p['municipios']),
                  'total': int(p['total']), 'places': [str(n) for n in p['nombres']]}
                 for p in props['ambito_partes']]
        areas.append({'name': str(props['nombre']), 'status': status, 'scope': scope, 'polygons': polygons})
    borders = [[point(p) for p in line] for line in source.get('provincias', [])]
    return {'version': 1, 'source': SOURCE, 'areas': areas, 'borders': borders}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--hide', action='append', default=[], metavar='NAME')
    args = parser.parse_args()
    result = export(json.loads(args.input.read_text(encoding='utf-8')), set(args.hide))
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
    print(f"Exported {len(result['areas'])} public coverage areas.")

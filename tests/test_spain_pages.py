"""Focused checks for bilingual navigation and public coverage boundaries."""
import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('coverage_builder', ROOT / 'scripts/build_spain_coverage.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
spec = importlib.util.spec_from_file_location('coverage_map_builder', ROOT / 'scripts/build_spain_coverage_map.py')
map_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(map_builder)


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids, self.refs, self.fields = [], [], []
        self.summaries = 0
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        for name in ['href', 'src']:
            if name in a:
                self.refs.append(a[name])
        if tag == 'summary':
            self.summaries += 1
        if tag in ['input', 'select', 'textarea'] and 'name' in a:
            self.fields.append(a['name'])


class SpainTests(unittest.TestCase):
    def test_bilingual_structure_links_and_contact_fields(self):
        pages = [ROOT / 'spain.html', ROOT / 'es/spain.html']
        parsed = [Page(p) for p in pages]
        self.assertEqual(parsed[0].ids, parsed[1].ids)
        for path, page in zip(pages, parsed):
            self.assertEqual(len(page.ids), len(set(page.ids)))
            self.assertEqual(page.summaries, 48)  # Research menu, 38 FAQs and 9 terms disclosures
            self.assertTrue({'country', 'purpose', 'name', 'email', 'places', 'period', 'client_status', 'request_type', 'goal', 'sources'} <= set(page.fields))
            for ref in page.refs:
                u = urlsplit(ref)
                if u.scheme:
                    continue
                target = (path.parent / u.path).resolve() if u.path else path
                self.assertTrue(target.is_file(), ref)
                if u.fragment:
                    self.assertIn(u.fragment, Page(target).ids, ref)

    def test_country_and_home_links(self):
        for directory in [ROOT, ROOT / 'es']:
            for name in ['index.html', 'service.html', 'statistics.html']:
                self.assertIn('spain.html', Page(directory / name).refs)
            self.assertIn('service.html', Page(directory / 'spain.html').refs)

    def test_public_dataset_is_minimal_and_unique(self):
        data = json.loads((ROOT / 'MAGENHA_DATA/spain_coverage.json').read_text())
        areas = {a['name'] for a in json.loads((ROOT / 'MAGENHA_DATA/spain_coverage_map.json').read_text())['areas']}
        self.assertEqual(set(data), {'version', 'localities'})
        self.assertTrue(data['localities'])
        pairs = set()
        for row in data['localities']:
            self.assertEqual(set(row), {'province', 'locality', 'status', 'area'})
            self.assertIn(row['status'], {'available', 'unavailable'})
            self.assertIn(row['area'], areas)
            pair = (row['province'], row['locality'])
            self.assertNotIn(pair, pairs)
            pairs.add(pair)

    def test_exporter_does_not_leak_internal_fields_or_overstate_rules(self):
        row = ['key', 'Town', 0, 40, -3] + [''] * 11 + ['Town']
        data = {'dioceses': ['Diocese'], 'provinces': ['Province'],
                'places': [['Town', 40, -3, 0]], 'rows': [row],
                'availability': [{'nivel': 'diocesis', 'diocesis': 'Diocese',
                    'disponible': 'si', 'nota': 'PRIVATE', 'via': 'PRIVATE'}]}
        def export():
            return builder.export('const D = '+json.dumps(data)+';')
        self.assertEqual(export()['localities'], [
            {'province': 'Province', 'locality': 'Town', 'status': 'available', 'area': 'Diocese'}])
        self.assertNotIn('PRIVATE', json.dumps(export()))
        data['availability'].append({'nivel': 'parroquia', 'clave': 'key', 'disponible': 'no'})
        self.assertEqual(export()['localities'], [
            {'province': 'Province', 'locality': 'Town', 'status': 'unavailable', 'area': 'Diocese'}])
        data['rows'].append(['key2', 'Town', 0, 40, -3] + [''] * 11 + ['Town'])
        self.assertEqual(export()['localities'][0]['status'], 'available')  # any confirmed route wins
        data['rows'].pop()
        data['availability'][-1]['disponible'] = 'con reservas'
        self.assertEqual(export()['localities'], [])
        data['availability'].pop()
        data['availability'][0]['desde'] = '1800'
        self.assertEqual(export()['localities'], [])
        data['availability'][0].pop('desde')
        data['places'].append(['Town', 40, -3, 0])
        self.assertEqual(export()['localities'], [])
        data['places'] = [['Town', 40, -3, 0], ['Town', 38, -6, 0]]
        data['fixes'] = [{'accion': 'modificar', 'clave': 'key', 'lat': '38', 'lon': '-6'}]
        self.assertEqual(len(export()['localities']), 1)
        data['places'][1][3] = 1
        data['provinces'].append('Other')
        self.assertEqual(export()['localities'][0]['province'], 'Other')
        data['fixes'] = [{'accion': 'ocultar', 'clave': 'key'}]
        self.assertEqual(export()['localities'], [])

    def test_public_map_is_minimal(self):
        data = json.loads((ROOT / 'MAGENHA_DATA/spain_coverage_map.json').read_text())
        self.assertEqual(set(data), {'version', 'source', 'areas', 'borders'})
        self.assertTrue(data['areas'])
        for area in data['areas']:
            self.assertEqual(set(area), {'name', 'status', 'scope', 'polygons'})
            self.assertIn(area['status'], {'available', 'limited', 'unavailable'})
            for part in area['scope']:
                self.assertEqual(set(part), {'province', 'whole', 'municipalities', 'total', 'places'})

    def test_map_exporter_keeps_only_public_fields(self):
        ring = [[0, 0], [1, 0], [1, 1], [0, 0]]
        feature = {'properties': {'nombre': 'Diocese', 'servicio': 'si', 'diocesis': 'PRIVATE', 'nota': 'PRIVATE',
                                  'ambito_partes': [{'provincia': 'P', 'toda': True, 'municipios': 2, 'total': 2, 'nombres': []}]},
                   'geometry': {'coordinates': [[ring]]}}
        other = lambda name, service: {**feature, 'properties': {**feature['properties'], 'nombre': name, 'servicio': service}}
        out = map_builder.export({'features': [feature, other('Unknown', 'x')], 'sin_servicio': [other('No', 'no')]})
        self.assertEqual([(a['name'], a['status']) for a in out['areas']], [('Diocese', 'available'), ('No', 'unavailable')])
        self.assertNotIn('PRIVATE', json.dumps(out))
        self.assertEqual(map_builder.export({'features': [feature]}, {'Diocese'})['areas'], [])


if __name__ == '__main__':
    unittest.main()

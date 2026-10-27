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
        self.assertEqual(set(data), {'version', 'localities'})
        self.assertTrue(data['localities'])
        pairs = set()
        for row in data['localities']:
            self.assertEqual(set(row), {'province', 'locality', 'status'})
            self.assertEqual(row['status'], 'available')
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
            {'province': 'Province', 'locality': 'Town', 'status': 'available'}])
        self.assertNotIn('PRIVATE', json.dumps(export()))
        data['availability'].append({'nivel': 'parroquia', 'clave': 'key', 'disponible': 'no'})
        self.assertEqual(export()['localities'], [])
        data['availability'].pop()
        data['availability'][0]['desde'] = '1800'
        self.assertEqual(export()['localities'], [])
        data['availability'][0].pop('desde')
        data['places'].append(['Town', 40, -3, 0])
        self.assertEqual(export()['localities'], [])


if __name__ == '__main__':
    unittest.main()

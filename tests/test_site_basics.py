"""Site-wide basics: sharing previews, icons, light logos, sitemap, robots and the 404 page."""
import re
import unittest
import xml.dom.minidom
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['index', 'spain', 'service', 'statistics', 'cuba']
PAGES = [ROOT / f'{n}.html' for n in NAMES] + [ROOT / 'es' / f'{n}.html' for n in NAMES]


class Head(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.meta, self.links, self.imgs, self.nav = {}, {}, [], []
        self._in_nav = False
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and (a.get('property') or a.get('name')):
            self.meta[a.get('property') or a.get('name')] = a.get('content')
        if tag == 'link' and a.get('rel'):
            self.links[a['rel']] = a.get('href')
        if tag == 'img':
            self.imgs.append(a)
        if tag == 'nav' and 'site-nav' in (a.get('class') or ''):
            self._in_nav = True

    def handle_endtag(self, tag):
        if tag == 'nav':
            self._in_nav = False

    def handle_data(self, data):
        if self._in_nav and data.strip():
            self.nav.append(data.strip())


class SiteBasicsTests(unittest.TestCase):
    def test_every_page_has_a_complete_sharing_preview(self):
        self.assertTrue((ROOT / 'og-image.jpg').is_file())
        for page in PAGES:
            h = Head(page)
            with self.subTest(page=page.relative_to(ROOT)):
                for key in ['og:type', 'og:site_name', 'og:title', 'og:description', 'og:url', 'og:image', 'og:image:alt',
                            'og:locale', 'twitter:card']:
                    self.assertTrue(h.meta.get(key), key)
                self.assertEqual(h.meta['og:url'], h.links['canonical'])
                self.assertEqual(h.meta['og:image'], 'https://magenha.org/og-image.jpg')
                self.assertEqual(h.meta['og:description'], h.meta['description'])
                self.assertEqual(h.meta['og:locale'], 'es_ES' if page.parent.name == 'es' else 'en_US')

    def test_icons_and_light_logos(self):
        for page in PAGES:
            h = Head(page)
            with self.subTest(page=page.relative_to(ROOT)):
                for rel in ['icon', 'apple-touch-icon']:
                    self.assertTrue((page.parent / h.links[rel]).resolve().is_file(), rel)
                # the 294 KB original is only allowed as the home hero illustration
                heavy = [i for i in h.imgs if i.get('src', '').endswith('/logo.png') or i.get('src') == 'logo.png']
                allowed = 1 if page.stem == 'index' else 0
                self.assertLessEqual(len(heavy), allowed)
                self.assertTrue(all(i.get('width') == '439' for i in heavy))

    def test_navigation_labels_match_across_pages(self):
        menus = {page: Head(page).nav for page in PAGES}
        for lang_pages in (PAGES[:5], PAGES[5:]):
            first = menus[lang_pages[0]]
            for page in lang_pages[1:]:
                self.assertEqual(menus[page], first, page.relative_to(ROOT))

    def test_sitemap_lists_every_canonical_page(self):
        doc = xml.dom.minidom.parse(str(ROOT / 'sitemap.xml'))
        locs = {n.firstChild.data for n in doc.getElementsByTagName('loc')}
        self.assertEqual(locs, {Head(p).links['canonical'] for p in PAGES})
        self.assertIn('Sitemap: https://magenha.org/sitemap.xml', (ROOT / 'robots.txt').read_text())

    def test_404_links_resolve_from_the_site_root(self):
        text = (ROOT / '404.html').read_text(encoding='utf-8')
        refs = re.findall(r'(?:href|src)="([^"]+)"', text)
        self.assertTrue(refs)
        for ref in refs:
            u = urlsplit(ref)
            if u.scheme:
                continue
            self.assertTrue(ref.startswith('/'), f'{ref}: must be root-relative')
            target = ROOT / u.path.lstrip('/')
            if u.path.endswith('/'):
                target = target / 'index.html'
            self.assertTrue(target.is_file(), ref)


    def test_every_local_link_and_anchor_resolves(self):
        ids = {}
        def page_ids(path):
            if path not in ids:
                ids[path] = set(re.findall(r'\bid="([^"]+)"', path.read_text(encoding='utf-8')))
            return ids[path]
        for page in PAGES:
            text = page.read_text(encoding='utf-8')
            for ref in re.findall(r'(?:href|src)="([^"]+)"', text):
                u = urlsplit(ref.replace('&amp;', '&'))
                if u.scheme or ref.startswith('mailto:'):
                    continue
                target = (page.parent / u.path).resolve() if u.path else page
                if u.path.endswith('/'):
                    target = target / 'index.html'
                with self.subTest(page=page.relative_to(ROOT), ref=ref):
                    self.assertTrue(target.is_file())
                    if u.fragment and target.suffix == '.html':
                        self.assertIn(u.fragment, page_ids(target))

if __name__ == '__main__':
    unittest.main()

"""Checks for the bilingual «Genealogy in Cuba» page: researcher cards, exact rating-form links and public ratings."""
import json
import unicodedata
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = {'en': ROOT / 'cuba.html', 'es': ROOT / 'es/cuba.html'}
RATINGS = ROOT / 'MAGENHA_DATA/cuba_researchers_ratings.json'
FORM = 'https://docs.google.com/forms/d/e/1FAIpQLScii5HHssRipUgv0L75o6Za05v8MHyt6XHAD_72PaJWtHqB0w/viewform?usp=pp_url&entry.1128160678='
RATE_LINKS = {  # exactly the prefilled links supplied by the owner (one form, one preselected researcher each)
    'lz_flores': FORM + 'L.Z.+Flores',
    'yumurigen': FORM + 'Yumurigen',
    'genesis_cuba': FORM + 'G%C3%A9nesis+Cuba',
    'magenha': FORM + 'Mapa+Geneal%C3%B3gico+de+Haplogrupos+(MAGENHA)',
}
# Public addresses shared with each researcher (cuba.html#<anchor>, es/cuba.html#<anchor>): never rename them.
PERMALINKS = {'genesis_cuba': 'genesis-cuba', 'lz_flores': 'lz-flores', 'magenha': 'magenha', 'yumurigen': 'yumurigen'}
OWN = 'magenha'   # MAGENHA's own entry: no independence notice, a red «no new requests» notice instead
SUGGEST_FORM = 'https://docs.google.com/forms/d/e/1FAIpQLScU7KNUAJjjg-7YLSh8cqpxVzErE-y85svE0p9ZIXLVGLYwCw/viewform'
# External research resources (static, no ratings): id → (category, Spanish page link, English page link).
# FamilySearch and Cuba Research Project have a language prefix; the English page uses their English address.
RESOURCES = {
    'cuban-genealogy-club': ('genealogy', 'https://www.cubangenclub.org/databases/', None),
    'familysearch': ('genealogy', 'https://www.familysearch.org/es/search/collection/4375851',
                     'https://www.familysearch.org/search/collection/4375851'),
    'cubagenweb': ('genealogy', 'https://www.cubagenweb.org/', None),
    'cuba-research-project': ('genealogy', 'https://cubaresearchproject.com/es/search', 'https://cubaresearchproject.com/search'),
    'endangered-archives': ('archives', 'https://eap.bl.uk/', None),
    'slave-societies': ('archives', 'https://www.slavesocieties.org/collections?name=Cuba', None),
    'pares-migration': ('archives', 'https://pares.cultura.gob.es/MovimientosMigratorios/', None),
    'hurtado-collection': ('libraries', 'https://ufdc.ufl.edu/ifiuhurtado', None),
    'cuban-heritage-collection': ('libraries', 'https://www.library.miami.edu/chc/digitalcollections.html', None),
    'dloc': ('libraries', 'https://www.dloc.com/', None),
}
NO_LOGO = {'pares-migration'}   # no logo supplied: neutral archive mark
EAP_PROJECTS = ['https://eap.bl.uk/project/EAP955', 'https://eap.bl.uk/project/EAP184', 'https://eap.bl.uk/project/EAP843']
RESOURCE_TEXT = {
    'en': ('Resources for Researching Your Cuban Roots', '(opens in a new tab)',
           'The resources listed here belong to institutions and projects independent of MAGENHA.'),
    'es': ('Recursos para investigar tus raíces cubanas', '(se abre en una pestaña nueva)',
           'Los recursos aquí presentados pertenecen a instituciones y proyectos independientes de MAGENHA.'),
}
LABELS = {
    'en': {'rate': 'Rate this service', 'spain': 'Continue my genealogical research in Spain', 'suggest': 'Suggest a researcher',
           'notice': 'Independent researcher or organization.', 'own': 'MAGENHA’s own service',
           'closed': 'Not accepting new clients in Cuba.'},
    'es': {'rate': 'Valorar este servicio', 'spain': 'Continuar mi investigación genealógica en España',
           'suggest': 'Sugerir un investigador', 'notice': 'Investigador u organización independiente.',
           'own': 'Servicio propio de MAGENHA', 'closed': 'No acepta nuevos clientes en Cuba.'},
}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids, self.refs, self.cards, self.links, self.resources = [], [], [], [], []
        self._card, self._tag, self._a, self._res = None, [], None, None
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        for name in ['href', 'src']:
            if a.get(name):
                self.refs.append(a[name])
        if tag == 'article' and 'data-researcher' in a:
            self._card = {'id': a['data-researcher'], 'anchor': a.get('id'), 'hidden': 'hidden' in a, 'name': '', 'rate': [],
                          'contacts': [], 'text': '', 'permalink': []}
            self.cards.append(self._card)
        if tag == 'article' and 'data-resource' in a:
            category = next((at['data-category'] for _, at in reversed(self._tag) if at.get('data-category')), None)
            self._res = {'id': a['data-resource'], 'category': category, 'links': [], 'img': [], 'empty_logo': False}
            self.resources.append(self._res)
        if tag == 'a':
            self._a = {'href': a.get('href'), 'class': a.get('class') or '', 'hidden': 'hidden' in a, 'text': '', 'attrs': a,
                       'in_index': any('page-index' in (attrs_.get('class') or '').split() for _, attrs_ in self._tag)}
            self.links.append(self._a)
            if self._res is not None:
                self._res['links'].append(self._a)
            if self._card is not None:
                if 'data-card-link' in a:
                    self._card['permalink'].append(a.get('href'))
                elif 'researcher-card__rate' in self._a['class']:
                    self._card['rate'].append(self._a)
                elif self._a['href'] and self._a['href'].startswith(('mailto:', 'https://wa.me/', 'https://')):
                    self._card['contacts'].append(self._a['href'])
        if self._res is not None and tag == 'img':
            self._res['img'].append(a.get('src'))
        if self._res is not None and 'resource-card__logo--empty' in (a.get('class') or ''):
            self._res['empty_logo'] = True
        self._tag.append((tag, a))

    def handle_endtag(self, tag):
        if tag == 'article':
            self._card = None
            self._res = None
        if tag == 'a':
            self._a = None
        while self._tag and self._tag.pop()[0] != tag:
            pass

    def handle_data(self, data):
        if self._a is not None:
            self._a['text'] += data
        if self._card is not None:
            self._card['text'] += data
            if any(t == 'h3' for t, _ in self._tag):
                self._card['name'] += data.strip()


def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)).casefold()


class CubaPageTests(unittest.TestCase):
    def setUp(self):
        self.pages = {lang: Page(path) for lang, path in PAGES.items()}

    def test_bilingual_structure_and_local_links(self):
        self.assertEqual(self.pages['en'].ids, self.pages['es'].ids)
        for lang, page in self.pages.items():
            path = PAGES[lang]
            self.assertEqual(len(page.ids), len(set(page.ids)), lang)
            for ref in page.refs:
                u = urlsplit(ref)
                if u.scheme:
                    continue
                target = (path.parent / u.path).resolve() if u.path else path
                self.assertTrue(target.is_file(), f'{lang}: {ref}')
                if u.fragment and target.suffix == '.html':
                    self.assertIn(u.fragment, Page(target).ids, f'{lang}: {ref}')

    def test_language_switch_points_to_the_other_version(self):
        self.assertIn('es/cuba.html', self.pages['en'].refs)
        self.assertIn('../cuba.html', self.pages['es'].refs)

    def test_cards_match_in_both_languages_in_alphabetical_order(self):
        en, es = self.pages['en'].cards, self.pages['es'].cards
        self.assertEqual([c['id'] for c in en], [c['id'] for c in es])
        self.assertEqual(set(c['id'] for c in en), set(RATE_LINKS))
        for lang, cards in self.pages.items():
            names = [c['name'] for c in cards.cards]
            self.assertEqual(names, sorted(names, key=fold), f'{lang}: not alphabetical, would read as a ranking')
            for card in cards.cards:
                self.assertTrue(card['name'], card['id'])
                self.assertTrue(card['contacts'], card['id'])
                if card['id'] == OWN:
                    self.assertIn(LABELS[lang]['own'], card['text'])
                    self.assertIn(LABELS[lang]['closed'], card['text'])
                    self.assertNotIn(LABELS[lang]['notice'], card['text'])
                else:
                    self.assertIn(LABELS[lang]['notice'], card['text'], card['id'])
                    self.assertNotIn(LABELS[lang]['closed'], card['text'], card['id'])
        self.assertEqual([c['contacts'] for c in en], [c['contacts'] for c in es])  # same contacts, untranslated

    def test_every_entry_has_a_stable_shareable_link(self):
        for lang, page in self.pages.items():
            self.assertEqual({c['id']: c['anchor'] for c in page.cards}, PERMALINKS, lang)
            for card in page.cards:
                self.assertEqual(card['permalink'], [], 'the addresses are handed out privately, not shown')
                index = [link['href'] for link in page.links if link['in_index']]
                self.assertIn('#' + card['anchor'], index, f'{lang}: not in «On this page»')

    def test_rate_buttons_open_the_exact_prefilled_form(self):
        for lang, page in self.pages.items():
            for card in page.cards:
                self.assertEqual(len(card['rate']), 1, f'{lang}: {card["id"]}')
                button = card['rate'][0]
                self.assertEqual(button['href'], RATE_LINKS[card['id']], f'{lang}: {card["id"]}')
                self.assertEqual(button['text'].strip(), LABELS[lang]['rate'])

    def test_public_ratings_hold_only_average_and_count(self):
        data = json.loads(RATINGS.read_text(encoding='utf-8'))
        self.assertEqual(set(data), set(RATE_LINKS))
        for rid, entry in data.items():
            self.assertEqual(set(entry), {'average_rating', 'rating_count'}, rid)
            count, average = entry['rating_count'], entry['average_rating']
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)
            if count == 0:
                self.assertIsNone(average, f'{rid}: no ratings must be null, never 0')
            else:
                self.assertTrue(1 <= average <= 5, rid)
        for lang, page in self.pages.items():
            url = [r for r in page.refs if r.endswith('.json')]
            self.assertFalse(url)  # read through data-ratings-url, checked below
            self.assertIn('MAGENHA_DATA/cuba_researchers_ratings.json', PAGES[lang].read_text(encoding='utf-8'))

    def test_spain_link_and_pending_suggestion_form(self):
        for lang, page in self.pages.items():
            spain = [a for a in page.links if a['text'].strip() == LABELS[lang]['spain']]
            self.assertTrue(spain, lang)
            self.assertTrue(all(a['href'] == 'spain.html' for a in spain), lang)
            suggest = [a for a in page.links if 'data-suggest-form' in a['attrs']]
            self.assertEqual(len(suggest), 1, lang)
            self.assertEqual(suggest[0]['text'].strip(), LABELS[lang]['suggest'])
            # hidden in the HTML; cuba.js shows it with the configured link (never a made-up one)
            self.assertTrue(suggest[0]['hidden'], lang)
            self.assertFalse(urlsplit(suggest[0]['href']).scheme, lang)
        self.assertIn(f'const SUGGEST_FORM_URL = "{SUGGEST_FORM}";', (ROOT / 'cuba.js').read_text(encoding='utf-8'))

    def test_every_page_links_to_the_cuba_page(self):
        for directory in [ROOT, ROOT / 'es']:
            for name in ['index.html', 'service.html', 'spain.html', 'statistics.html', 'cuba.html']:
                self.assertIn('cuba.html', Page(directory / name).refs, f'{directory.name}/{name}')


    def test_resources_in_both_languages_by_category(self):
        for lang, page in self.pages.items():
            self.assertEqual([r['id'] for r in page.resources], list(RESOURCES), lang)
            for res in page.resources:
                category, es_url, en_url = RESOURCES[res['id']]
                self.assertEqual(res['category'], category, f'{lang}: {res["id"]}')
                main = [link['href'] for link in res['links'] if link['href'] not in EAP_PROJECTS]
                self.assertEqual(main, [es_url if lang == 'es' or en_url is None else en_url], f'{lang}: {res["id"]}')
            eap = next(r for r in page.resources if r['id'] == 'endangered-archives')
            self.assertEqual([link['href'] for link in eap['links'] if link['href'] in EAP_PROJECTS], EAP_PROJECTS, lang)

    def test_every_resource_has_its_logo_or_the_neutral_mark(self):
        for lang, page in self.pages.items():
            for res in page.resources:
                if res['id'] in NO_LOGO:
                    self.assertEqual((res['img'], res['empty_logo']), ([], True), res['id'])
                else:
                    self.assertEqual(len(res['img']), 1, res['id'])
                    self.assertTrue(res['img'][0].endswith(f"images/directory/{res['id']}-logo." + res['img'][0].rsplit('.', 1)[1]))

    def test_resource_links_open_safely_and_say_so(self):
        for lang, page in self.pages.items():
            for res in page.resources:
                for link in res['links']:
                    self.assertTrue(link['href'].startswith('https://'), link['href'])
                    self.assertEqual(link['attrs'].get('target'), '_blank', link['href'])
                    self.assertTrue({'noopener', 'noreferrer'} <= set(link['attrs'].get('rel', '').split()), link['href'])
                    self.assertIn(RESOURCE_TEXT[lang][1], link['text'], link['href'])

    def test_resources_section_sits_between_directory_and_suggestions(self):
        for lang, page in self.pages.items():
            ids = page.ids
            self.assertLess(ids.index('directory'), ids.index('resources'), lang)
            self.assertLess(ids.index('resources'), ids.index('suggest'), lang)
            self.assertIn('#resources', [link['href'] for link in page.links if link['in_index']], lang)
            text = PAGES[lang].read_text(encoding='utf-8')
            self.assertIn(RESOURCE_TEXT[lang][0], text)
            self.assertIn(RESOURCE_TEXT[lang][2], text)

if __name__ == '__main__':
    unittest.main()

import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


SITE_ROOT = Path(__file__).resolve().parents[1]
STATISTICS_PAGES = (SITE_ROOT / "statistics.html", SITE_ROOT / "es" / "statistics.html")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.scripts = []
        self.statistics_root = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        for attribute in ("href", "src"):
            if attributes.get(attribute):
                self.references.append(attributes[attribute])
        if tag == "script" and attributes.get("src"):
            self.scripts.append(attributes["src"])
        if "data-statistics-app" in attributes:
            self.statistics_root = attributes


def parse_page(path):
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class StatisticsPageTests(unittest.TestCase):
    def test_statistics_pages_have_unique_ids_and_local_runtime_data(self):
        for page in STATISTICS_PAGES:
            with self.subTest(page=page.relative_to(SITE_ROOT)):
                parsed = parse_page(page)
                self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
                self.assertIsNotNone(parsed.statistics_root)
                for attribute in ("data-statistics-url", "data-map-url"):
                    reference = parsed.statistics_root[attribute]
                    self.assertIn("MAGENHA_DATA/haplogroup_statistics/", reference)
                    self.assertTrue((page.parent / reference).resolve().is_file())

    def test_statistics_pages_have_no_remote_javascript_dependency(self):
        for page in STATISTICS_PAGES:
            with self.subTest(page=page.relative_to(SITE_ROOT)):
                parsed = parse_page(page)
                self.assertTrue(parsed.scripts)
                self.assertTrue(all(not urlparse(source).scheme for source in parsed.scripts))

    def test_local_page_assets_resolve(self):
        for page in STATISTICS_PAGES:
            with self.subTest(page=page.relative_to(SITE_ROOT)):
                for reference in parse_page(page).references:
                    parsed = urlparse(reference)
                    if parsed.scheme or reference.startswith(("#", "mailto:")):
                        continue
                    target = (page.parent / parsed.path).resolve()
                    self.assertTrue(target.is_file(), f"{page}: missing {reference}")

    def test_statistics_are_linked_from_every_existing_navigation(self):
        pages = (
            SITE_ROOT / "index.html",
            SITE_ROOT / "service.html",
            SITE_ROOT / "es" / "index.html",
            SITE_ROOT / "es" / "service.html",
        )
        for page in pages:
            with self.subTest(page=page.relative_to(SITE_ROOT)):
                self.assertIn('href="statistics.html"', page.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

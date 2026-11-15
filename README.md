# MAGENHA public website

This repository contains the static website published at [magenha.org](https://magenha.org).

## Structure

- `index.html` — public homepage
- `service.html` — genealogy services, the Y-DNA/mtDNA lineage program, first-contact form, and terms
- `statistics.html` — browser-based country and haplogroup statistics explorer
- `es/index.html` — Spanish homepage
- `es/service.html` — Spanish services, lineage program, first-contact form, and terms
- `es/statistics.html` — Spanish statistics explorer
- `style.css` — shared responsive styles
- `script.js` — mobile navigation and small progressive enhancements
- `statistics.css` / `statistics.js` — explorer styles and browser-side calculations/map rendering
- `cuba.html` / `es/cuba.html` — Genealogy in Cuba: end of new Cuba cases and the directory of independent researchers
- `cuba.css` / `cuba.js` — researcher and resource cards, star ratings and the suggestion-form link
- `images/` — every picture the pages use, as light web copies:
  - `images/brand/` — `logo-header.png` (header/footer) and `logo-card.jpg` (MAGENHA's Cuba card)
  - `images/directory/` — researcher logos (`<id>-256.jpg`) and resource logos (`<id>-logo.jpg|png`)
  - `images/scenes/` — section illustrations: `dna-hero`, `spain-hero`, `statistics-hero`, `cuba-hero`
    (with `-900` copies for phones), `lineage-tree`, `cta-path`, `rootscast-banner`, `spain-region`,
    `footer`, `process`, `record-lineage` (background of the home scene), the transparent header roots
    `roots-left.png` / `roots-right.png`, and the episode thumbnail `rootscast-26.jpg`
- `_fuentes/` — local only, git-ignored: the owner's original images (2–3 MB each) the web copies
  come from, and working notes. Never published; regenerate a web copy from here when a picture changes
- `MAGENHA_DATA/haplogroup_statistics/` — disclosure-controlled aggregate statistics and local map geometry served by GitHub Pages
- `scripts/build_haplogroup_statistics.py` — optional offline data refresh utility
- `logo.png` — MAGENHA brand image
- `favicon.png`, `apple-touch-icon.png` — icons made from `logo.png`, which pages no longer load
- `og-image.jpg` — 1200×630 sharing preview used by every page's Open Graph tags
- `404.html`, `sitemap.xml`, `robots.txt` — GitHub Pages error page and search-engine files
- `CNAME` — custom-domain configuration for GitHub Pages

The public site is maintained on the `stare-branch` branch. No build step or package installation is required.

## Preview locally

From this directory, run:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000` in a browser.

The statistics explorer uses `fetch()`, so it must be previewed through this
local server rather than opened directly as a `file://` URL.

## Refresh the statistics data

The published site has no build step. Its aggregate JSON is committed under
`MAGENHA_DATA` and works as-is on GitHub Pages. Rare country/lineage cells are
removed by the generator before publication; the source CSV remains outside
this repository. To rebuild the public files from the legacy-derived source in
the unified workspace, run:

```bash
python3 scripts/build_haplogroup_statistics.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

See `MAGENHA_DATA/haplogroup_statistics/README.md` for the data boundaries,
methodology, map provenance, and optional path arguments.

## Publish

Commit reviewed changes to `stare-branch` and push that branch to GitHub. Keep `CNAME` unchanged so the custom domain continues to work.

## Spain documentary research (ES/EN)

- `spain.html` / `es/spain.html`: independent Spain service, 38 FAQs,
  Spain-specific terms and the existing browser-only email composer.
- `spain.css` / `spain.js`: country navigation, accessible disclosures and the
  coverage search and map. The search answers as you type with one verdict (green
  "viable" with a smile, red "not viable" with a sad face, amber when it depends on
  the locality or the place is not in our data) and a card per locality; a card or
  the verdict's "see it on the map" highlights its diocese. The map is green where we
  research and hatched red where we do not for now, with a tooltip, a legend and a
  detail card per diocese. Both pages load them as `spain.css?v=…` / `spain.js?v=…`:
  change the version in both pages whenever either file changes, or browsers keep the
  old copy (the two JSON files are always revalidated). Shared branding, navigation,
  page index, form styles and mail draft/copy handling remain in `style.css` / `script.js`.
- `MAGENHA_DATA/spain_coverage_map.json`: the coverage map (every diocese, with
  service or without it for now): area name, status (`available`, `limited`,
  `unavailable`), per-province scope, rounded outlines and province borders only.
  Municipal boundaries: Instituto Geográfico Nacional, CC BY 4.0, via es-atlas 0.6.0.
  Built by `scripts/build_spain_coverage_map.py` from the internal `cobertura.geojson`;
  `--hide "Area name"` leaves an area off the public map.
- `MAGENHA_DATA/spain_coverage.json`: public list containing only province,
  locality, status (`available` or `unavailable`) and area (its diocese, as named on
  the map), one locality per line. No contacts, archive inventories, coordinates,
  internal notes, reasons, rates or access arrangements are included.

MAGENHA no longer offers research services in Cuba (removed from the public site on
2026-11-13). Spain is the only research service: the navigation's "Research in Spain"
link and every inquiry, terms, process and coverage link lead to `spain.html`.
`service.html` / `es/service.html` keep only the Y-DNA/mtDNA Lineage Research Program,
its program terms and the mission and outreach section. The language switch preserves
the section anchor.

Coverage is a conservative snapshot of confirmed operational availability, not a
promise of document survival, access or appointments. Province search lists
covered localities and does not assert province-wide coverage. Unlisted places
require individual assessment; failed data loading is not reported as no coverage.
The current export (2026-10-28) covers every diocese except Zamora, Tenerife
(San Cristóbal de La Laguna), Tarazona, Salamanca and Ávila, shown as not viable:
67 map areas (62 viable, 5 not viable), 11,639 viable and 879 not viable localities.
A locality with any confirmed route is viable. Locality names
must match the internal place catalogue and coordinates within 3 km, uniquely;
ambiguous matches, places without a province and conditional availability rules are
excluded (those places get the amber "individual assessment" answer). The explorer's own corrections apply: a hidden parish is dropped and a
moved one is matched where it now lies.

To refresh from a separately maintained internal explorer, run:

```bash
python3 scripts/build_spain_coverage.py /path/to/internal/explorador.html MAGENHA_DATA/spain_coverage.json
```

and the map from the internal coverage map (`cobertura.py` in the explorer's folder):

```bash
python3 scripts/build_spain_coverage_map.py /path/to/internal/Output/cobertura/cobertura.geojson MAGENHA_DATA/spain_coverage_map.json
```

Keep the inputs outside this public repository. Rebuild the internal explorer from
exported availability changes first: browser-only edits are not read. Review the
public diff and operational availability before publishing. The exporter writes
only its explicit public field allowlist; it does not copy the original explorer.

## Genealogy in Cuba (ES/EN)

- `cuba.html` / `es/cuba.html`: the notice that new clients for Cuba were accepted until
  15 November 2026 inclusive (current and former clients keep being served as normal,
  open cases and new requests alike), a prominent link to `spain.html`,
  the directory of independent researchers and the "suggest a researcher" section.
  Every footer links to it ("Genealogy in Cuba" / "Genealogía en Cuba"). Both pages
  load `cuba.css?v=…` / `cuba.js?v=…`: change the version in both whenever either file changes.
- Cards are static HTML, one `<article class="researcher-card" data-researcher="<id>">`
  per researcher, in alphabetical order (never by rating), with the same IDs and
  contacts in both languages. Description, contacts, logo and rating link are static;
  only the stars come from the JSON. Logos: `images/directory/<id>-256.jpg` (web
  copies, at most 256 px; originals in `_fuentes/`). Without
  an authorised image, use the neutral placeholder:
  `<div class="researcher-card__media researcher-card__media--empty" aria-hidden="true">` + an icon.
  MAGENHA itself is also listed (ID `magenha`, reusing `logo.png`) so its clients can rate it with
  the same form and method: its card has a red `researcher-card__closed` notice (no new requests
  in Cuba from 16 November 2026) and a note on being our own service instead of the independence notice.
- Every entry has a permanent address that is shared with its researcher so they can
  pass it to their clients: `https://magenha.org/es/cuba.html#<anchor>` (and
  `cuba.html#<anchor>` in English) with the anchors `genesis-cuba`, `lz-flores`, `magenha`
  and `yumurigen`. **Never rename an `<article>`'s `id`** (the test guards them). Each entry
  is listed under "On this page" and is outlined in gold when opened from its address. The
  addresses are not shown on the page: the owner keeps them privately in
  `projects_unification/MAGENHA_DATA/reviews_cuba/enlaces/enlaces_investigadores.xlsx`.
- "Rate this service" opens the exact prefilled link of the single Google Form
  (`entry.1128160678` preselects the researcher). Keep the links as supplied.
- `MAGENHA_DATA/cuba_researchers_ratings.json`: only `{id: {average_rating, rating_count}}`.
  `null` and `0` mean no ratings ("No ratings yet", never 0/5); if the file cannot be
  loaded the page says ratings are unavailable. It is generated by MAGENHA Manager
  (magenha_codes/economics_research_manager, `manager/web_ratings.py`) from the private
  Google Forms export in `projects_unification/MAGENHA_DATA/reviews_cuba/`: button
  "Actualizar valoraciones de web_site" (Más → Web pública: valoraciones) or
  `~/.venv/bin/python3 tools/update_web_site.py`. It never commits or pushes. Never copy
  the export, comments or e-mails into this repository.
- Research resources (`#resources`, between the directory and the suggestion form): ten
  external archives, libraries and genealogy projects in three groups (genealogy and
  indexes, archives and digitized records, libraries and historical collections). They are
  static `<article class="resource-card" data-resource="<id>">` blocks inside each
  `resource-group`, with no ratings and no economics link. To add, edit or remove one,
  change both pages and `RESOURCES` in `tests/test_cuba_page.py` (same ids, order and
  links). External links open in a new tab with `rel="noopener noreferrer"` and a
  hidden "(opens in a new tab)". The English page uses the English addresses of
  FamilySearch and Cuba Research Project. Each card shows the logo supplied by the owner
  (`images/directory/<id>-logo.jpg|png`, web copies of at most 400×128 px; originals in
  `_fuentes/`); a resource without logo gets the neutral
  `resource-card__logo--empty` mark. Each group heading keeps its neutral icon.
- The English Cuba page uses American spelling (organization, digitized, specializing).
- Suggestion form: its Google Forms link is `SUGGEST_FORM_URL` at the top of `cuba.js`
  (one place for both languages; bump `cuba.js?v=` in both pages after changing it). The
  script reveals the "Suggest a researcher" button with it; if it were emptied, the button
  would stay hidden and an "available soon" note would show. It is not automated: economics
  never reads this second form.
- A new researcher: the option in the Google Form, a line in `RESEARCHERS`
  (`manager/web_ratings.py`), an `<article>` in both pages and its link in
  `tests/test_cuba_page.py`.

## Visual refresh (November 2026)

- **Versions.** Every page loads its CSS and JS as `file?v=…` (`style.css`, `script.js`,
  `spain.*`, `statistics.*`, `cuba.*`). Change the version in every page that loads a file
  whenever that file changes, or returning visitors keep the old copy.
- **Header.** On the desktop bar the first "Home"/"Inicio" link is hidden (the logo leads home;
  it stays in the mobile menu) and the bar keeps a 2rem gap, so the Spanish menu never touches
  the wordmark. `main { overflow-x: clip }` stops decorative circles from widening the page.
- **Sharing and search.** Each page has Open Graph/Twitter tags (`og:url` = canonical,
  `og-image.jpg`); `sitemap.xml` lists the ten canonical pages with their language pairs;
  `404.html` uses root-relative links only. `tests/test_site_basics.py` guards all of this,
  and every local link and anchor of every page.
- **Motion.** `.reveal` blocks below the screen when a page opens get a short entrance
  (`reveal--pending` → `is-visible`); nothing on screen blinks, and with reduced motion, without
  JavaScript or in print everything is simply shown. The coverage map pulses twice, statistics
  bars grow when a table is redrawn, and the map colours fade.
- **Mobile index.** Under 980 px the "On this page" index becomes a sticky bar under the header
  that names the current section and opens the list (Spain, DNA program, Cuba). The current
  section is the last one whose top passed 30% of the screen.
- **Home.** The eyebrow states the offer; one main action (coverage in Spain) and one secondary
  (statistics); three intent links replace the old trust strip; the large logo is replaced by an
  inline SVG scene of a **fictitious** example (baptism → person → tree → direct maternal line),
  drawn once. Never use images of real archive books there.
- **DNA program.** `[data-lineage-explainer]`: an interactive four-generation tree with the direct
  paternal (Y-DNA, copper) and maternal (mtDNA, teal) lines.
- **Spain.** Coverage is the first section. A verdict's action copies the place searched into the
  first-contact form's "Relevant place(s)". `#deliverables` has a fictitious, tabbed sample
  (`[data-tabs]`, the same María Josefa example as the home scene).
- **Statistics.** The hero says what can be explored; a short caveat sits right above the
  explorer with the full explanation folded below it; the three figures sit side by side on phones.
- **Rootscast.** The support panel (home, DNA program, Spain) opens with a featured episode. To
  change it, replace `images/scenes/rootscast-26.jpg` and the `rootscast-feature` link and texts in those six pages.

## Illustrated sections (November 2026)

- The owner's illustrations live as web copies in `images/scenes/` (originals in `_fuentes/`):
  DNA program hero (`.dna-hero`, dark), Spain and Cuba heroes (`.service-hero--light` with
  `.spain-hero` / `.cuba-hero`), statistics hero, home lineage picture (`.lineage-picture`), home
  call-to-action picture (`.cta-card__image`, with `srcset`), Spain region card, the Rootscast
  banner behind the support panel title (`.support-panel__intro`) and the footer background.
- The header bar carries two transparent root drawings (one beside the logo, one hanging on the
  right; only the logo's on phones), the counterpart of the footer picture. The home process
  section shows `.process-intro__image` under its introduction, and the home scene draws on
  `record-lineage.jpg` with dark tags behind its kicker and «fictitious example» label.
- On phones, busy illustrations (DNA, Spain, Rootscast) become a band under the text (an `::after`
  with the picture's own aspect ratio), so they never sit behind words; the footer shows its picture
  as a band at the bottom.
- Pictures must be text-free (the pages give every text in both languages), keep the left side calm
  for headings, show only fictitious material (never real archive books) and stay in the site palette.

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
- `MAGENHA_DATA/haplogroup_statistics/` — disclosure-controlled aggregate statistics and local map geometry served by GitHub Pages
- `scripts/build_haplogroup_statistics.py` — optional offline data refresh utility
- `logo.png` — MAGENHA brand image
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
- `spain.css` / `spain.js`: country navigation, accessible disclosures and
  locality/province coverage search. Shared branding, navigation, page index,
  form styles and mail draft/copy handling remain in `style.css` / `script.js`.
- `MAGENHA_DATA/spain_coverage_map.json`: the coverage map (dioceses and zones with
  service): area name, status, per-province scope, rounded outlines and province
  borders only. Municipal boundaries: Instituto Geográfico Nacional, CC BY 4.0,
  via es-atlas 0.6.0. Built by `scripts/build_spain_coverage_map.py` from the internal
  `cobertura.geojson`; `--hide "Area name"` leaves an area off the public map.
- `MAGENHA_DATA/spain_coverage.json`: public allowlist containing only province,
  locality and an available status. No contacts, archive inventories, coordinates,
  internal notes, rates or access arrangements are included.

Cuba remains at `service.html` / `es/service.html`, with its existing content and
terms. The shared Research navigation groups Cuba and Spain; both service pages also
offer a country selector. The language switch preserves the section anchor.

Coverage is a conservative snapshot of confirmed operational availability, not a
promise of document survival, access or appointments. Province search lists
covered localities and does not assert province-wide coverage. Unlisted places
require individual assessment; failed data loading is not reported as no coverage.
The current export (2026-10-27) uses 18 confirmed diocesan availability rules
(Girona, Tarragona, Madrid, Alcalá de Henares, Getafe, Toledo, Sigüenza-Guadalajara,
Ávila, Segovia, Calahorra y La Calzada-Logroño, Oviedo, Pamplona y Tudela,
San Sebastián, Bilbao, Vitoria, Sevilla, Cádiz y Ceuta, Jerez de la Frontera) plus
the parishes of the island of Fuerteventura. Locality names
must match the internal place catalogue and coordinates within 3 km, uniquely;
ambiguous matches and conditional availability rules are excluded.

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

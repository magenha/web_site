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

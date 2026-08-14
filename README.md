# MAGENHA public website

This repository contains the static website published at [magenha.org](https://magenha.org).

## Structure

- `index.html` — public homepage
- `service.html` — genealogy services, the Y-DNA/mtDNA lineage program, first-contact form, and terms
- `es/index.html` — Spanish homepage
- `es/service.html` — Spanish services, lineage program, first-contact form, and terms
- `style.css` — shared responsive styles
- `script.js` — mobile navigation and small progressive enhancements
- `logo.png` — MAGENHA brand image
- `CNAME` — custom-domain configuration for GitHub Pages

The public site is maintained on the `stare-branch` branch. No build step or package installation is required.

## Preview locally

From this directory, run:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000` in a browser.

## Publish

Commit reviewed changes to `stare-branch` and push that branch to GitHub. Keep `CNAME` unchanged so the custom domain continues to work.

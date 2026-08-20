# Haplogroup statistics data

This directory contains the static, aggregate data used by the public
haplogroup-statistics page.  GitHub Pages can serve both files directly; no
Flask server, database, pandas, geopandas, or Plotly runtime is required.

## Published files

- `statistics.json` contains country/type observation denominators plus
  disclosure-controlled exact and broad-group count rows.
  `observation_columns` and `group_observation_columns` declare the position
  of every value in the compact `observations` and `group_observations` rows.
  Country markers are `[longitude, latitude]`.
- `countries.geojson` contains the local Natural Earth country polygons.  Join
  a feature to the statistics with `feature.properties.alpha2`.

No source CSV, spreadsheet, database, pickle, source-category breakdown, name,
DNA-relative identifier, or other person-level file is published here.  The
private input CSV's original filename is not included in provenance.

## Disclosure control

Published cells must have at least **5 observations**, and their country/type
denominator must have at least **30 observations**.  Suppression happens in the
generator, before the JSON is written; it is not merely hidden by the browser.

The generator also uses complementary suppression:

1. Within an eligible country/type stratum, broad groups below 5 are omitted.
   If that would leave exactly one positive group hidden, the smallest otherwise
   publishable group is omitted too.
2. Exact haplogroups are considered only inside a published broad group.  Exact
   cells below 5 are omitted.  If that would leave exactly one positive exact
   haplogroup hidden, the smallest otherwise publishable exact cell is omitted
   too.

This prevents one hidden sibling from being recovered by subtracting published
siblings from its retained parent denominator.  Omitted cells are absent from
the corresponding index as well as the observation rows.  A blank or absent
result means **no estimate is published**; it is not evidence that the true
count is zero.  Country/type denominators retain all accepted observations so
the UI can explain when a stratum is insufficient and can calculate a published
cell's percentage consistently.

## Methodology

One accepted row of the private legacy-derived CSV is counted as one
haplogroup/country observation.  Identical `(type, haplogroup, group, country)`
combinations are collapsed to one aggregate row with an integer count.  A
haplogroup's broad group is its upper-case leading letters.

Percentages are intentionally not baked into the file.  For a selected country
and type, calculate:

```text
published count / countries[].observation_counts[type] * 100
```

This same-country, same-type denominator corrects the legacy implementation,
which sometimes divided a Y-DNA or mtDNA count by the country's combined total.
The `observation_counts.total` value is for display only.  These counts describe
observations, not independent or representative population samples.

These convenience observations come mainly from volunteer-contributed 23andMe
DNA Relatives exports, plus a small number of MAGENHA observations.  They are a
non-random convenience sample, can contain relatives or repeated lineages, and
must not be interpreted as representative population frequencies.

## Map matching and coverage

Natural Earth `ISO_A2_EH` is the primary join key, with `ISO_A2` and `WB_A2` as
fallbacks.  This avoids the old country-name matching failures and handles
Natural Earth's `-99` values for places such as France, Norway, Taiwan, and
Kosovo.  Every dataset country also receives a marker: Natural Earth's
`LABEL_X`/`LABEL_Y` is preferred, and the first coordinate in IANA tzdb's
`zone.tab` is used for small territories omitted from the 1:110m polygons.

The map is derived from **Natural Earth Admin 0 – Countries, 1:110m, version
5.1.1**, which is public domain.  Natural Earth boundaries reflect that
project's cartographic policy and do not express a MAGENHA position on disputed
territories.  Marker fallbacks are derived from the public-domain IANA Time Zone
Database `zone.tab` file.

- Natural Earth: <https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/>
- Natural Earth terms: <https://www.naturalearthdata.com/about/terms-of-use/>
- IANA tzdb: <https://www.iana.org/time-zones>

SHA-256 hashes for the private CSV, Natural Earth SHP and DBF, and IANA
`zone.tab` inputs are recorded in `statistics.json`; the map repeats its SHP and
DBF hashes.  Both artifacts record the WGS84 longitude/latitude (EPSG:4326)
coordinate assumption.  These values make input drift detectable without
publishing the private source data or its original filename.

## Regeneration

From the `web_site` directory in the unified workspace:

```bash
python3 scripts/build_haplogroup_statistics.py
python3 -m unittest discover -s tests -p 'test_haplogroup_statistics_data.py'
```

The defaults point to the legacy-derived private CSV and Natural Earth files in
the adjacent `old_magenha_core_public` directory and to
`/usr/share/zoneinfo/zone.tab`.  Use `--source-csv`, `--natural-earth-shp`,
`--natural-earth-dbf`, `--zone-tab`, and `--output-dir` when those inputs live
elsewhere.  The generator uses only the Python standard library and writes the
two JSON files atomically.  A standalone public-site checkout can serve the
committed artifacts but intentionally cannot reproduce the private source CSV.

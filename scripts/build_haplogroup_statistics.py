#!/usr/bin/env python3
"""Build static haplogroup statistics and map data for the public website.

The legacy application calculated these views dynamically with pandas, Flask,
and Plotly.  This converter performs that work once and writes browser-friendly
JSON which can be served unchanged by GitHub Pages.  It deliberately uses only
the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
SITE_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = SITE_ROOT.parent
LEGACY_FILES = (
    WORKSPACE_ROOT
    / "old_magenha_core_public"
    / "magenha-dev-Scripts"
    / "static"
    / "files"
)
DEFAULT_SOURCE_CSV = (
    LEGACY_FILES
    / "haplogroupstatistics"
    / "Output"
    / "23andmestatistics.csv"
)
DEFAULT_NATURAL_EARTH_BASE = (
    LEGACY_FILES
    / "geopandas-110m_cultural"
    / "ne_110m_admin_0_countries"
)
DEFAULT_OUTPUT_DIR = SITE_ROOT / "MAGENHA_DATA" / "haplogroup_statistics"

VALID_TYPES = ("YDNA", "mtDNA")
TYPE_ORDER = {value: index for index, value in enumerate(VALID_TYPES)}
OBSERVATION_COLUMNS = ("type", "haplogroup", "group", "alpha2", "count")
GROUP_OBSERVATION_COLUMNS = ("type", "group", "alpha2", "count")
ISO2_RE = re.compile(r"^[A-Z]{2}$")
GROUP_RE = re.compile(r"^([A-Za-z]+)")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

SCHEMA_VERSION = 2
MINIMUM_CELL_COUNT = 5
MINIMUM_COUNTRY_TYPE_OBSERVATION_COUNT = 30
COORDINATE_REFERENCE_SYSTEM = "WGS84 longitude/latitude (EPSG:4326)"
PROVENANCE_INPUT_KEYS = (
    "source_csv",
    "natural_earth_shp",
    "natural_earth_dbf",
    "zone_tab",
)

# Natural Earth 1:110m intentionally omits many small territories.  These
# localized labels cover the data codes which do not have their own feature in
# the source layer.  New codes still receive their ISO-2 code as a safe label.
COUNTRY_NAME_FALLBACKS: Mapping[str, Mapping[str, str]] = {
    "AG": {"en": "Antigua and Barbuda", "es": "Antigua y Barbuda"},
    "AW": {"en": "Aruba", "es": "Aruba"},
    "BB": {"en": "Barbados", "es": "Barbados"},
    "BQ": {
        "en": "Bonaire, Sint Eustatius and Saba",
        "es": "Bonaire, San Eustaquio y Saba",
    },
    "CV": {"en": "Cabo Verde", "es": "Cabo Verde"},
    "CW": {"en": "Curaçao", "es": "Curazao"},
    "GD": {"en": "Grenada", "es": "Granada"},
    "GF": {"en": "French Guiana", "es": "Guayana Francesa"},
    "GI": {"en": "Gibraltar", "es": "Gibraltar"},
    "GU": {"en": "Guam", "es": "Guam"},
    "HK": {"en": "Hong Kong", "es": "Hong Kong"},
    "JE": {"en": "Jersey", "es": "Jersey"},
    "KN": {"en": "Saint Kitts and Nevis", "es": "San Cristóbal y Nieves"},
    "KY": {"en": "Cayman Islands", "es": "Islas Caimán"},
    "MQ": {"en": "Martinique", "es": "Martinica"},
    "MT": {"en": "Malta", "es": "Malta"},
    "MU": {"en": "Mauritius", "es": "Mauricio"},
    "PM": {"en": "Saint Pierre and Miquelon", "es": "San Pedro y Miquelón"},
    "SC": {"en": "Seychelles", "es": "Seychelles"},
    "SG": {"en": "Singapore", "es": "Singapur"},
    "TO": {"en": "Tonga", "es": "Tonga"},
    "VC": {
        "en": "Saint Vincent and the Grenadines",
        "es": "San Vicente y las Granadinas",
    },
    "VI": {
        "en": "United States Virgin Islands",
        "es": "Islas Vírgenes de los Estados Unidos",
    },
}


class DataError(ValueError):
    """Raised when an input or generated artifact is internally inconsistent."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def haplogroup_group(haplogroup: str) -> str:
    match = GROUP_RE.match(haplogroup.strip())
    if not match:
        raise DataError(f"haplogroup has no leading letter group: {haplogroup!r}")
    return match.group(1).upper()


def read_observations(
    path: Path,
) -> tuple[Counter[tuple[str, str, str, str]], int]:
    """Read categorical source rows and combine identical observations."""

    counts: Counter[tuple[str, str, str, str]] = Counter()
    required = {"type_haplogroup", "haplogroup", "country"}

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = set(reader.fieldnames or ())
        missing = required - fieldnames
        if missing:
            raise DataError(
                f"{path}: missing required CSV columns: {', '.join(sorted(missing))}"
            )

        row_count = 0
        for line_number, row in enumerate(reader, start=2):
            haplogroup_type = (row.get("type_haplogroup") or "").strip()
            haplogroup = (row.get("haplogroup") or "").strip()
            alpha2 = (row.get("country") or "").strip().upper()

            if haplogroup_type not in VALID_TYPES:
                raise DataError(
                    f"{path}:{line_number}: unsupported haplogroup type "
                    f"{haplogroup_type!r}"
                )
            if not haplogroup:
                raise DataError(f"{path}:{line_number}: empty haplogroup")
            if not ISO2_RE.fullmatch(alpha2):
                raise DataError(
                    f"{path}:{line_number}: invalid ISO alpha-2 code {alpha2!r}"
                )

            group = haplogroup_group(haplogroup)
            supplied_group = (row.get("Group") or "").strip().upper()
            if supplied_group and supplied_group != group:
                raise DataError(
                    f"{path}:{line_number}: Group {supplied_group!r} does not "
                    f"match haplogroup {haplogroup!r}"
                )

            counts[(haplogroup_type, haplogroup, group, alpha2)] += 1
            row_count += 1

    if not row_count:
        raise DataError(f"{path}: no observation rows")
    return counts, row_count


def read_dbf(path: Path) -> list[dict[str, str] | None]:
    """Read the text/numeric fields needed from a dBASE III/IV table."""

    with path.open("rb") as source:
        header = source.read(32)
        if len(header) != 32:
            raise DataError(f"{path}: truncated DBF header")
        record_count = struct.unpack_from("<I", header, 4)[0]
        header_length = struct.unpack_from("<H", header, 8)[0]
        record_length = struct.unpack_from("<H", header, 10)[0]
        if header_length < 33 or record_length < 1:
            raise DataError(f"{path}: invalid DBF dimensions")

        descriptor_count = (header_length - 33) // 32
        fields: list[tuple[str, int]] = []
        for _ in range(descriptor_count):
            descriptor = source.read(32)
            if len(descriptor) != 32:
                raise DataError(f"{path}: truncated DBF field descriptor")
            name = descriptor[:11].split(b"\0", 1)[0].decode("ascii")
            fields.append((name, descriptor[16]))

        source.seek(header_length)
        records: list[dict[str, str] | None] = []
        for record_index in range(record_count):
            raw = source.read(record_length)
            if len(raw) != record_length:
                raise DataError(
                    f"{path}: truncated DBF record {record_index + 1}/{record_count}"
                )
            if raw[:1] == b"*":
                records.append(None)
                continue
            position = 1
            record: dict[str, str] = {}
            for name, width in fields:
                value = raw[position : position + width]
                position += width
                record[name] = value.decode("utf-8", errors="replace").strip(" \0")
            records.append(record)
    return records


def _signed_area(ring: Sequence[Sequence[float]]) -> float:
    return sum(
        first[0] * second[1] - second[0] * first[1]
        for first, second in zip(ring, ring[1:])
    ) / 2.0


def _point_in_ring(point: Sequence[float], ring: Sequence[Sequence[float]]) -> bool:
    x, y = point
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
        previous = current
    return inside


def _orient_ring(
    ring: list[list[float]], *, counterclockwise: bool
) -> list[list[float]]:
    is_counterclockwise = _signed_area(ring) > 0
    if is_counterclockwise != counterclockwise:
        return list(reversed(ring))
    return ring


def _rings_to_geometry(rings: Iterable[list[list[float]]]) -> dict[str, object]:
    """Convert shapefile rings into RFC 7946 Polygon/MultiPolygon coordinates."""

    usable = [ring for ring in rings if len(ring) >= 4 and _signed_area(ring) != 0]
    if not usable:
        raise DataError("polygon record contains no usable rings")

    # ESRI polygons use clockwise exterior rings.  A rare counter-clockwise
    # ring is attached as a hole to the smallest containing exterior.
    exteriors = [ring for ring in usable if _signed_area(ring) < 0]
    possible_holes = [ring for ring in usable if _signed_area(ring) > 0]
    if not exteriors:
        largest = max(usable, key=lambda value: abs(_signed_area(value)))
        exteriors = [largest]
        possible_holes = [ring for ring in usable if ring is not largest]

    polygons: list[list[list[list[float]]]] = [
        [_orient_ring(exterior, counterclockwise=True)] for exterior in exteriors
    ]
    exterior_areas = [abs(_signed_area(exterior)) for exterior in exteriors]

    for ring in possible_holes:
        containers = [
            index
            for index, exterior in enumerate(exteriors)
            if _point_in_ring(ring[0], exterior)
        ]
        if containers:
            owner = min(containers, key=lambda index: exterior_areas[index])
            polygons[owner].append(_orient_ring(ring, counterclockwise=False))
        else:
            # Defensive fallback for a source which does not follow ESRI ring
            # orientation.  Preserve it as an exterior instead of dropping it.
            exteriors.append(ring)
            exterior_areas.append(abs(_signed_area(ring)))
            polygons.append([_orient_ring(ring, counterclockwise=True)])

    if len(polygons) == 1:
        return {"type": "Polygon", "coordinates": polygons[0]}
    return {"type": "MultiPolygon", "coordinates": polygons}


def read_polygon_shapes(
    path: Path, precision: int = 5
) -> list[dict[str, object] | None]:
    """Read Polygon records from an ESRI shapefile without GIS dependencies."""

    geometries: list[dict[str, object] | None] = []
    with path.open("rb") as source:
        header = source.read(100)
        if len(header) != 100 or struct.unpack_from(">I", header, 0)[0] != 9994:
            raise DataError(f"{path}: invalid shapefile header")

        while True:
            record_header = source.read(8)
            if not record_header:
                break
            if len(record_header) != 8:
                raise DataError(f"{path}: truncated shapefile record header")
            _, content_words = struct.unpack(">II", record_header)
            content = source.read(content_words * 2)
            if len(content) != content_words * 2:
                raise DataError(f"{path}: truncated shapefile record")

            shape_type = struct.unpack_from("<I", content, 0)[0]
            if shape_type == 0:
                geometries.append(None)
                continue
            if shape_type not in (5, 15, 25):
                raise DataError(
                    f"{path}: expected Polygon shape, found type {shape_type}"
                )
            part_count, point_count = struct.unpack_from("<II", content, 36)
            parts_offset = 44
            points_offset = parts_offset + part_count * 4
            required_length = points_offset + point_count * 16
            if required_length > len(content):
                raise DataError(f"{path}: invalid polygon record dimensions")

            starts = list(
                struct.unpack_from(f"<{part_count}I", content, parts_offset)
            )
            starts.append(point_count)
            points: list[list[float]] = []
            for point_index in range(point_count):
                x, y = struct.unpack_from(
                    "<dd", content, points_offset + point_index * 16
                )
                rounded_x = round(x, precision)
                rounded_y = round(y, precision)
                points.append(
                    [
                        0.0 if rounded_x == 0 else rounded_x,
                        0.0 if rounded_y == 0 else rounded_y,
                    ]
                )

            rings: list[list[list[float]]] = []
            for start, stop in zip(starts, starts[1:]):
                ring: list[list[float]] = []
                for point in points[start:stop]:
                    if not ring or point != ring[-1]:
                        ring.append(point)
                if ring and ring[0] != ring[-1]:
                    ring.append(ring[0])
                rings.append(ring)
            geometries.append(_rings_to_geometry(rings))
    return geometries


def stable_iso2(record: Mapping[str, str]) -> str | None:
    """Return Natural Earth's stable ISO-2 code, including its -99 fixes."""

    for field in ("ISO_A2_EH", "ISO_A2", "WB_A2"):
        candidate = record.get(field, "").strip().upper()
        if ISO2_RE.fullmatch(candidate):
            return candidate
    return None


def _country_names(record: Mapping[str, str], alpha2: str) -> dict[str, str]:
    fallback = COUNTRY_NAME_FALLBACKS.get(alpha2, {})
    english = (
        record.get("NAME_EN")
        or record.get("NAME_LONG")
        or record.get("ADMIN")
        or fallback.get("en")
        or alpha2
    )
    spanish = record.get("NAME_ES") or fallback.get("es") or english
    return {"en": english, "es": spanish}


def load_natural_earth(
    dbf_path: Path,
    shp_path: Path,
    version: str,
    *,
    dbf_sha256: str,
    shp_sha256: str,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    records = read_dbf(dbf_path)
    geometries = read_polygon_shapes(shp_path)
    if len(records) != len(geometries):
        raise DataError(
            "Natural Earth DBF/shapefile record count mismatch: "
            f"{len(records)} != {len(geometries)}"
        )

    features: list[dict[str, object]] = []
    metadata: dict[str, dict[str, object]] = {}
    for record, geometry in zip(records, geometries):
        if record is None or geometry is None:
            continue
        alpha2 = stable_iso2(record)
        if alpha2 is None:
            continue
        if alpha2 in metadata:
            raise DataError(f"duplicate Natural Earth ISO alpha-2 code: {alpha2}")

        names = _country_names(record, alpha2)
        label: list[float] | None = None
        try:
            longitude = float(record.get("LABEL_X", ""))
            latitude = float(record.get("LABEL_Y", ""))
            if math.isfinite(longitude) and math.isfinite(latitude):
                label = [round(longitude, 5), round(latitude, 5)]
        except ValueError:
            pass

        metadata[alpha2] = {"names": names, "label": label}
        features.append(
            {
                "type": "Feature",
                "properties": {"alpha2": alpha2, "names": names},
                "geometry": geometry,
            }
        )

    features.sort(key=lambda feature: feature["properties"]["alpha2"])
    document: dict[str, object] = {
        "type": "FeatureCollection",
        "metadata": {
            "source": "Natural Earth Admin 0 – Countries, 1:110m",
            "version": version,
            "license": "Public domain",
            "coordinate_reference_system": COORDINATE_REFERENCE_SYSTEM,
            "inputs": {
                "natural_earth_shp": {
                    "file": shp_path.name,
                    "sha256": shp_sha256,
                },
                "natural_earth_dbf": {
                    "file": dbf_path.name,
                    "sha256": dbf_sha256,
                },
            },
            "generated_by": "scripts/build_haplogroup_statistics.py",
        },
        "features": features,
    }
    return document, metadata


def parse_zone_coordinate(value: str) -> list[float]:
    match = re.fullmatch(
        r"([+-])(\d{2})(\d{2})(\d{2})?([+-])(\d{3})(\d{2})(\d{2})?",
        value,
    )
    if not match:
        raise DataError(f"invalid zone.tab coordinate: {value!r}")
    (
        latitude_sign,
        latitude_degrees,
        latitude_minutes,
        latitude_seconds,
        longitude_sign,
        longitude_degrees,
        longitude_minutes,
        longitude_seconds,
    ) = match.groups()

    latitude = int(latitude_degrees) + int(latitude_minutes) / 60
    longitude = int(longitude_degrees) + int(longitude_minutes) / 60
    if latitude_seconds:
        latitude += int(latitude_seconds) / 3600
    if longitude_seconds:
        longitude += int(longitude_seconds) / 3600
    if latitude_sign == "-":
        latitude = -latitude
    if longitude_sign == "-":
        longitude = -longitude
    return [round(longitude, 5), round(latitude, 5)]


def read_zone_tab(path: Path) -> dict[str, list[float]]:
    """Read the first representative timezone coordinate for each ISO-2 code."""

    coordinates: dict[str, list[float]] = {}
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip() or line.startswith("#"):
                continue
            columns = line.rstrip("\n").split("\t")
            if len(columns) < 3:
                raise DataError(f"{path}:{line_number}: malformed zone.tab row")
            alpha2 = columns[0].upper()
            if ISO2_RE.fullmatch(alpha2) and alpha2 not in coordinates:
                coordinates[alpha2] = parse_zone_coordinate(columns[1])
    return coordinates


def _published_values(counts: Mapping[str, int]) -> set[str]:
    """Apply primary and one-cell complementary suppression to sibling cells."""

    published = {
        value for value, count in counts.items() if count >= MINIMUM_CELL_COUNT
    }
    hidden = set(counts) - published
    if len(hidden) == 1 and published:
        secondary = min(
            published,
            key=lambda value: (counts[value], value.casefold(), value),
        )
        published.remove(secondary)
    return published


def apply_disclosure_control(
    observation_counts: Mapping[tuple[str, str, str, str], int],
    country_type_counts: Mapping[str, Mapping[str, int]],
) -> tuple[
    Counter[tuple[str, str, str, str]],
    Counter[tuple[str, str, str]],
]:
    """Return exact and group cells which are safe to publish."""

    group_children: defaultdict[tuple[str, str], Counter[str]] = defaultdict(
        Counter
    )
    exact_children: defaultdict[tuple[str, str, str], Counter[str]] = defaultdict(
        Counter
    )
    for (
        haplogroup_type,
        haplogroup,
        group,
        alpha2,
    ), count in observation_counts.items():
        group_children[(haplogroup_type, alpha2)][group] += count
        exact_children[(haplogroup_type, group, alpha2)][haplogroup] += count

    published_exact: Counter[tuple[str, str, str, str]] = Counter()
    published_groups: Counter[tuple[str, str, str]] = Counter()
    for (haplogroup_type, alpha2), group_counts in group_children.items():
        denominator = country_type_counts.get(alpha2, {}).get(haplogroup_type, 0)
        if denominator < MINIMUM_COUNTRY_TYPE_OBSERVATION_COUNT:
            continue

        for group in _published_values(group_counts):
            group_count = group_counts[group]
            published_groups[(haplogroup_type, group, alpha2)] = group_count
            haplogroup_counts = exact_children[(haplogroup_type, group, alpha2)]
            for haplogroup in _published_values(haplogroup_counts):
                published_exact[(haplogroup_type, haplogroup, group, alpha2)] = (
                    haplogroup_counts[haplogroup]
                )
    return published_exact, published_groups


def file_provenance(path: Path) -> dict[str, str]:
    return {"file": path.name, "sha256": sha256_file(path)}


def build_provenance(
    source_csv: Path,
    natural_earth_shp: Path,
    natural_earth_dbf: Path,
    zone_tab: Path,
    natural_earth_version_value: str,
) -> dict[str, object]:
    return {
        "inputs": {
            "source_csv": {
                "file": "private-source.csv",
                "sha256": sha256_file(source_csv),
            },
            "natural_earth_shp": file_provenance(natural_earth_shp),
            "natural_earth_dbf": file_provenance(natural_earth_dbf),
            "zone_tab": file_provenance(zone_tab),
        },
        "natural_earth": {
            "dataset": "Admin 0 – Countries, 1:110m",
            "version": natural_earth_version_value,
            "license": "Public domain",
        },
        "coordinate_reference_system": COORDINATE_REFERENCE_SYSTEM,
        "generated_by": "scripts/build_haplogroup_statistics.py",
    }


def build_statistics_document(
    observation_counts: Mapping[tuple[str, str, str, str], int],
    row_count: int,
    natural_earth_metadata: Mapping[str, Mapping[str, object]],
    zone_coordinates: Mapping[str, Sequence[float]],
    *,
    provenance: Mapping[str, object],
) -> dict[str, object]:
    country_type_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    totals_by_type: Counter[str] = Counter()

    for (
        haplogroup_type,
        haplogroup,
        group,
        alpha2,
    ), count in observation_counts.items():
        if haplogroup_type not in VALID_TYPES:
            raise DataError(
                f"unsupported aggregate haplogroup type: {haplogroup_type!r}"
            )
        if haplogroup_group(haplogroup) != group:
            raise DataError(f"aggregate group mismatch for {haplogroup!r}")
        if not ISO2_RE.fullmatch(alpha2):
            raise DataError(f"invalid aggregate country code: {alpha2!r}")
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise DataError("aggregate observation counts must be positive integers")
        country_type_counts[alpha2][haplogroup_type] += count
        totals_by_type[haplogroup_type] += count

    if row_count != sum(totals_by_type.values()):
        raise DataError("source row count does not match aggregate observations")

    published_exact, published_groups = apply_disclosure_control(
        observation_counts, country_type_counts
    )
    haplogroups: defaultdict[str, set[str]] = defaultdict(set)
    groups: defaultdict[str, set[str]] = defaultdict(set)
    for haplogroup_type, haplogroup, _group, _alpha2 in published_exact:
        haplogroups[haplogroup_type].add(haplogroup)
    for haplogroup_type, group, _alpha2 in published_groups:
        groups[haplogroup_type].add(group)

    countries: list[dict[str, object]] = []
    polygon_codes = set(natural_earth_metadata)
    for alpha2 in country_type_counts:
        earth = natural_earth_metadata.get(alpha2, {})
        fallback = COUNTRY_NAME_FALLBACKS.get(alpha2, {})
        earth_names = earth.get("names", {})
        if not isinstance(earth_names, Mapping):
            earth_names = {}
        english = str(earth_names.get("en") or fallback.get("en") or alpha2)
        spanish = str(earth_names.get("es") or fallback.get("es") or english)

        label = earth.get("label")
        if (
            isinstance(label, Sequence)
            and not isinstance(label, (str, bytes))
            and len(label) == 2
        ):
            marker = [float(label[0]), float(label[1])]
            marker_source = "natural-earth-label"
        elif alpha2 in zone_coordinates:
            marker = [float(value) for value in zone_coordinates[alpha2]]
            marker_source = "tzdb-zone.tab"
        else:
            raise DataError(
                f"no Natural Earth label or zone.tab marker for data code {alpha2}"
            )

        by_type = country_type_counts[alpha2]
        observation_denominators = {value: by_type[value] for value in VALID_TYPES}
        observation_denominators["total"] = sum(observation_denominators.values())
        countries.append(
            {
                "alpha2": alpha2,
                "names": {"en": english, "es": spanish},
                "marker": marker,
                "marker_source": marker_source,
                "has_polygon": alpha2 in polygon_codes,
                "observation_counts": observation_denominators,
            }
        )

    countries.sort(
        key=lambda country: (country["names"]["en"].casefold(), country["alpha2"])
    )
    observations = [
        [haplogroup_type, haplogroup, group, alpha2, count]
        for (haplogroup_type, haplogroup, group, alpha2), count in sorted(
            published_exact.items(),
            key=lambda item: (
                TYPE_ORDER[item[0][0]],
                item[0][1].casefold(),
                item[0][1],
                item[0][3],
            ),
        )
    ]
    group_observations = [
        [haplogroup_type, group, alpha2, count]
        for (haplogroup_type, group, alpha2), count in sorted(
            published_groups.items(),
            key=lambda item: (
                TYPE_ORDER[item[0][0]],
                item[0][1].casefold(),
                item[0][1],
                item[0][2],
            ),
        )
    ]

    document: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "types": list(VALID_TYPES),
        "totals": {
            "observation_count": row_count,
            "country_count": len(countries),
            "published_exact_cell_count": len(observations),
            "published_group_cell_count": len(group_observations),
            "by_type": {value: totals_by_type[value] for value in VALID_TYPES},
        },
        "countries": countries,
        "haplogroups": {
            value: sorted(haplogroups[value], key=lambda item: (item.casefold(), item))
            for value in VALID_TYPES
        },
        "groups": {
            value: sorted(groups[value], key=lambda item: (item.casefold(), item))
            for value in VALID_TYPES
        },
        "observation_columns": list(OBSERVATION_COLUMNS),
        "observations": observations,
        "group_observation_columns": list(GROUP_OBSERVATION_COLUMNS),
        "group_observations": group_observations,
        "privacy": {
            "minimum_cell_count": MINIMUM_CELL_COUNT,
            "minimum_country_type_observation_count": (
                MINIMUM_COUNTRY_TYPE_OBSERVATION_COUNT
            ),
            "complementary_suppression": True,
            "suppressed_cells": "omitted",
            "denominators_include_suppressed_observations": True,
            "blank_semantics": "no published estimate; not evidence of zero",
        },
        "provenance": dict(provenance),
        "methodology": {
            "unit": "haplogroup-country observation (one accepted source CSV row)",
            "group_rule": "upper-case leading letters of haplogroup",
            "percentage_formula": (
                "published cell count / same-country same-type observation count * 100"
            ),
            "denominator_key": "countries[].observation_counts[type]",
            "disclosure_control": (
                "primary thresholds plus complementary suppression among sibling cells"
            ),
        },
    }
    validate_statistics_document(document)
    return document


def _valid_integer(value: object, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _valid_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _validate_names(value: object, label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != {"en", "es"}:
        raise DataError(f"invalid names for {label}")
    if not all(isinstance(value[key], str) and value[key] for key in ("en", "es")):
        raise DataError(f"empty names for {label}")


def _validate_file_provenance(value: object, label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != {"file", "sha256"}:
        raise DataError(f"invalid provenance entry for {label}")
    filename = value.get("file")
    digest = value.get("sha256")
    if (
        not isinstance(filename, str)
        or not filename
        or Path(filename).name != filename
        or not isinstance(digest, str)
        or not SHA256_RE.fullmatch(digest)
    ):
        raise DataError(f"invalid provenance values for {label}")


def _validate_statistics_provenance(value: object) -> None:
    if not isinstance(value, Mapping):
        raise DataError("generated statistics lacks provenance")
    inputs = value.get("inputs")
    if not isinstance(inputs, Mapping) or set(inputs) != set(PROVENANCE_INPUT_KEYS):
        raise DataError("generated statistics has incomplete input provenance")
    for key in PROVENANCE_INPUT_KEYS:
        _validate_file_provenance(inputs[key], key)
    natural_earth = value.get("natural_earth")
    if (
        not isinstance(natural_earth, Mapping)
        or natural_earth.get("dataset") != "Admin 0 – Countries, 1:110m"
        or not isinstance(natural_earth.get("version"), str)
        or not natural_earth.get("version")
        or natural_earth.get("license") != "Public domain"
    ):
        raise DataError("invalid Natural Earth provenance")
    if value.get("coordinate_reference_system") != COORDINATE_REFERENCE_SYSTEM:
        raise DataError("invalid coordinate reference system provenance")
    if value.get("generated_by") != "scripts/build_haplogroup_statistics.py":
        raise DataError("invalid statistics generator provenance")


def validate_statistics_document(document: Mapping[str, object]) -> None:
    if document.get("schema_version") != SCHEMA_VERSION:
        raise DataError("unsupported generated statistics schema")
    if document.get("types") != list(VALID_TYPES):
        raise DataError("unexpected generated haplogroup types")
    if document.get("observation_columns") != list(OBSERVATION_COLUMNS):
        raise DataError("unexpected exact observation columns")
    if document.get("group_observation_columns") != list(GROUP_OBSERVATION_COLUMNS):
        raise DataError("unexpected group observation columns")

    privacy = document.get("privacy")
    expected_privacy = {
        "minimum_cell_count": MINIMUM_CELL_COUNT,
        "minimum_country_type_observation_count": (
            MINIMUM_COUNTRY_TYPE_OBSERVATION_COUNT
        ),
        "complementary_suppression": True,
        "suppressed_cells": "omitted",
        "denominators_include_suppressed_observations": True,
        "blank_semantics": "no published estimate; not evidence of zero",
    }
    if privacy != expected_privacy:
        raise DataError("unexpected generated privacy policy")

    countries_value = document.get("countries")
    observations_value = document.get("observations")
    group_observations_value = document.get("group_observations")
    if (
        not isinstance(countries_value, list)
        or not isinstance(observations_value, list)
        or not isinstance(group_observations_value, list)
    ):
        raise DataError("generated statistics lacks required data arrays")

    countries: dict[str, Mapping[str, object]] = {}
    denominator_totals: Counter[str] = Counter()
    expected_country_fields = {
        "alpha2",
        "names",
        "marker",
        "marker_source",
        "has_polygon",
        "observation_counts",
    }
    for country in countries_value:
        if not isinstance(country, Mapping) or set(country) != expected_country_fields:
            raise DataError("invalid generated country metadata")
        alpha2 = country.get("alpha2")
        if not isinstance(alpha2, str) or not ISO2_RE.fullmatch(alpha2):
            raise DataError(f"invalid generated country code: {alpha2!r}")
        if alpha2 in countries:
            raise DataError(f"duplicate generated country code: {alpha2}")
        _validate_names(country.get("names"), alpha2)
        marker = country.get("marker")
        if (
            not isinstance(marker, list)
            or len(marker) != 2
            or not all(_valid_number(value) for value in marker)
            or not (-180 <= marker[0] <= 180 and -90 <= marker[1] <= 90)
        ):
            raise DataError(f"invalid marker for {alpha2}: {marker!r}")
        if country.get("marker_source") not in {
            "natural-earth-label",
            "tzdb-zone.tab",
        }:
            raise DataError(f"invalid marker source for {alpha2}")
        if not isinstance(country.get("has_polygon"), bool):
            raise DataError(f"invalid polygon flag for {alpha2}")
        counts = country.get("observation_counts")
        if not isinstance(counts, Mapping) or set(counts) != {*VALID_TYPES, "total"}:
            raise DataError(f"invalid observation denominators for {alpha2}")
        if not all(_valid_integer(counts[key]) for key in (*VALID_TYPES, "total")):
            raise DataError(f"invalid observation denominator values for {alpha2}")
        expected_total = sum(counts[value] for value in VALID_TYPES)
        if counts["total"] != expected_total or expected_total <= 0:
            raise DataError(f"observation denominator total mismatch for {alpha2}")
        for haplogroup_type in VALID_TYPES:
            denominator_totals[haplogroup_type] += counts[haplogroup_type]
        countries[alpha2] = country

    group_rows: dict[tuple[str, str, str], int] = {}
    group_sum_by_stratum: Counter[tuple[str, str]] = Counter()
    for row in group_observations_value:
        if not isinstance(row, list) or len(row) != 4:
            raise DataError(f"invalid generated group row: {row!r}")
        haplogroup_type, group, alpha2, count = row
        key = (haplogroup_type, group, alpha2)
        if (
            haplogroup_type not in VALID_TYPES
            or not isinstance(group, str)
            or not re.fullmatch(r"[A-Z]+", group)
            or alpha2 not in countries
            or not _valid_integer(count, minimum=MINIMUM_CELL_COUNT)
            or key in group_rows
        ):
            raise DataError(f"invalid generated group row: {row!r}")
        denominator = countries[alpha2]["observation_counts"][haplogroup_type]
        if denominator < MINIMUM_COUNTRY_TYPE_OBSERVATION_COUNT or count > denominator:
            raise DataError(f"disclosure threshold violation in group row: {row!r}")
        group_rows[key] = count
        group_sum_by_stratum[(alpha2, haplogroup_type)] += count

    exact_keys: set[tuple[str, str, str, str]] = set()
    exact_sum_by_parent: Counter[tuple[str, str, str]] = Counter()
    for row in observations_value:
        if not isinstance(row, list) or len(row) != 5:
            raise DataError(f"invalid generated exact row: {row!r}")
        haplogroup_type, haplogroup, group, alpha2, count = row
        key = (haplogroup_type, haplogroup, group, alpha2)
        parent = (haplogroup_type, group, alpha2)
        if (
            haplogroup_type not in VALID_TYPES
            or alpha2 not in countries
            or not isinstance(haplogroup, str)
            or haplogroup_group(haplogroup) != group
            or not _valid_integer(count, minimum=MINIMUM_CELL_COUNT)
            or key in exact_keys
            or parent not in group_rows
        ):
            raise DataError(f"invalid generated exact row: {row!r}")
        denominator = countries[alpha2]["observation_counts"][haplogroup_type]
        if denominator < MINIMUM_COUNTRY_TYPE_OBSERVATION_COUNT:
            raise DataError(f"disclosure threshold violation in exact row: {row!r}")
        exact_keys.add(key)
        exact_sum_by_parent[parent] += count

    for (alpha2, haplogroup_type), published_sum in group_sum_by_stratum.items():
        denominator = countries[alpha2]["observation_counts"][haplogroup_type]
        if published_sum > denominator or denominator - published_sum == 1:
            raise DataError(
                f"unsafe published group remainder for {alpha2}/{haplogroup_type}"
            )
    for parent, published_sum in exact_sum_by_parent.items():
        parent_total = group_rows[parent]
        if published_sum > parent_total or parent_total - published_sum == 1:
            raise DataError(f"unsafe published exact remainder for {parent!r}")

    expected_haplogroups = {
        value: sorted(
            {key[1] for key in exact_keys if key[0] == value},
            key=lambda item: (item.casefold(), item),
        )
        for value in VALID_TYPES
    }
    expected_groups = {
        value: sorted(
            {key[1] for key in group_rows if key[0] == value},
            key=lambda item: (item.casefold(), item),
        )
        for value in VALID_TYPES
    }
    if document.get("haplogroups") != expected_haplogroups:
        raise DataError("published haplogroup index mismatch")
    if document.get("groups") != expected_groups:
        raise DataError("published group index mismatch")

    expected_exact_order = sorted(
        observations_value,
        key=lambda row: (
            TYPE_ORDER[row[0]],
            row[1].casefold(),
            row[1],
            row[3],
        ),
    )
    expected_group_order = sorted(
        group_observations_value,
        key=lambda row: (
            TYPE_ORDER[row[0]],
            row[1].casefold(),
            row[1],
            row[2],
        ),
    )
    if observations_value != expected_exact_order:
        raise DataError("published exact rows are not deterministically ordered")
    if group_observations_value != expected_group_order:
        raise DataError("published group rows are not deterministically ordered")

    totals = document.get("totals")
    expected_total_fields = {
        "observation_count",
        "country_count",
        "published_exact_cell_count",
        "published_group_cell_count",
        "by_type",
    }
    if not isinstance(totals, Mapping) or set(totals) != expected_total_fields:
        raise DataError("generated statistics has invalid totals")
    expected_by_type = {value: denominator_totals[value] for value in VALID_TYPES}
    if totals.get("by_type") != expected_by_type:
        raise DataError("generated type total mismatch")
    if totals.get("observation_count") != sum(expected_by_type.values()):
        raise DataError("generated overall observation count mismatch")
    if totals.get("country_count") != len(countries):
        raise DataError("generated country count mismatch")
    if totals.get("published_exact_cell_count") != len(observations_value):
        raise DataError("generated exact cell count mismatch")
    if totals.get("published_group_cell_count") != len(group_observations_value):
        raise DataError("generated group cell count mismatch")

    methodology = document.get("methodology")
    if (
        not isinstance(methodology, Mapping)
        or methodology.get("denominator_key")
        != "countries[].observation_counts[type]"
    ):
        raise DataError("generated methodology mismatch")
    _validate_statistics_provenance(document.get("provenance"))


def _validate_ring(ring: object, alpha2: str, *, exterior: bool) -> None:
    if not isinstance(ring, list) or len(ring) < 4:
        raise DataError(f"invalid map ring for {alpha2}")
    positions: list[list[float]] = []
    for position in ring:
        if (
            not isinstance(position, list)
            or len(position) != 2
            or not all(_valid_number(value) for value in position)
            or not (-180 <= position[0] <= 180 and -90 <= position[1] <= 90)
        ):
            raise DataError(f"invalid map position for {alpha2}: {position!r}")
        positions.append(position)
    if positions[0] != positions[-1]:
        raise DataError(f"unclosed map ring for {alpha2}")
    if any(first == second for first, second in zip(positions, positions[1:])):
        raise DataError(f"duplicate consecutive map position for {alpha2}")
    if len({tuple(position) for position in positions[:-1]}) < 3:
        raise DataError(f"degenerate map ring for {alpha2}")
    area = _signed_area(positions)
    if area == 0 or (area > 0) != exterior:
        raise DataError(f"invalid map ring orientation for {alpha2}")


def validate_map_document(document: Mapping[str, object]) -> None:
    if document.get("type") != "FeatureCollection":
        raise DataError("generated map is not a FeatureCollection")
    metadata = document.get("metadata")
    if not isinstance(metadata, Mapping):
        raise DataError("generated map lacks metadata")
    if (
        metadata.get("source") != "Natural Earth Admin 0 – Countries, 1:110m"
        or not isinstance(metadata.get("version"), str)
        or not metadata.get("version")
        or metadata.get("license") != "Public domain"
        or metadata.get("coordinate_reference_system")
        != COORDINATE_REFERENCE_SYSTEM
        or metadata.get("generated_by")
        != "scripts/build_haplogroup_statistics.py"
    ):
        raise DataError("invalid generated map metadata")
    inputs = metadata.get("inputs")
    map_input_keys = {"natural_earth_shp", "natural_earth_dbf"}
    if not isinstance(inputs, Mapping) or set(inputs) != map_input_keys:
        raise DataError("generated map has incomplete input provenance")
    for key in map_input_keys:
        _validate_file_provenance(inputs[key], key)

    features = document.get("features")
    if not isinstance(features, list) or not features:
        raise DataError("generated map has no features")
    seen: set[str] = set()
    for feature in features:
        if not isinstance(feature, Mapping) or feature.get("type") != "Feature":
            raise DataError("invalid generated map feature")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, Mapping) or not isinstance(geometry, Mapping):
            raise DataError("generated map feature lacks properties or geometry")
        alpha2 = properties.get("alpha2")
        if not isinstance(alpha2, str) or not ISO2_RE.fullmatch(alpha2):
            raise DataError(f"invalid map ISO alpha-2 code: {alpha2!r}")
        if alpha2 in seen:
            raise DataError(f"duplicate map ISO alpha-2 code: {alpha2}")
        _validate_names(properties.get("names"), alpha2)
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        if geometry_type == "Polygon":
            polygons = [coordinates]
        elif geometry_type == "MultiPolygon":
            polygons = coordinates
        else:
            raise DataError(f"invalid map geometry for {alpha2}")
        if not isinstance(polygons, list) or not polygons:
            raise DataError(f"empty map geometry for {alpha2}")
        for polygon in polygons:
            if not isinstance(polygon, list) or not polygon:
                raise DataError(f"empty map polygon for {alpha2}")
            for ring_index, ring in enumerate(polygon):
                _validate_ring(ring, alpha2, exterior=ring_index == 0)
        seen.add(alpha2)


def validate_cross_document_coverage(
    statistics: Mapping[str, object], map_document: Mapping[str, object]
) -> None:
    map_codes = {
        feature["properties"]["alpha2"] for feature in map_document["features"]
    }
    for country in statistics["countries"]:
        if country["has_polygon"] != (country["alpha2"] in map_codes):
            raise DataError(f"map coverage flag mismatch for {country['alpha2']}")
        # A marker is mandatory even when 1:110m has no polygon for a territory.
        if len(country["marker"]) != 2:
            raise DataError(f"missing map marker for {country['alpha2']}")


def write_json(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as destination:
        json.dump(
            document,
            destination,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        destination.write("\n")
    os.replace(temporary, path)


def natural_earth_version(shapefile: Path) -> str:
    version_file = shapefile.with_suffix(".VERSION.txt")
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "unknown"


def default_zone_tab() -> Path:
    candidates = (
        Path("/usr/share/zoneinfo/zone.tab"),
        Path("/usr/share/lib/zoneinfo/tab/zone_sun.tab"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def build(
    source_csv: Path,
    natural_earth_dbf: Path,
    natural_earth_shp: Path,
    zone_tab: Path,
    output_dir: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    for path in (source_csv, natural_earth_dbf, natural_earth_shp, zone_tab):
        if not path.is_file():
            raise DataError(f"required input does not exist: {path}")

    version = natural_earth_version(natural_earth_shp)
    provenance = build_provenance(
        source_csv,
        natural_earth_shp,
        natural_earth_dbf,
        zone_tab,
        version,
    )
    observations, row_count = read_observations(source_csv)
    provenance_inputs = provenance["inputs"]
    map_document, earth_metadata = load_natural_earth(
        natural_earth_dbf,
        natural_earth_shp,
        version,
        dbf_sha256=provenance_inputs["natural_earth_dbf"]["sha256"],
        shp_sha256=provenance_inputs["natural_earth_shp"]["sha256"],
    )
    zone_coordinates = read_zone_tab(zone_tab)
    statistics = build_statistics_document(
        observations,
        row_count,
        earth_metadata,
        zone_coordinates,
        provenance=provenance,
    )
    validate_map_document(map_document)
    validate_cross_document_coverage(statistics, map_document)
    write_json(output_dir / "statistics.json", statistics)
    write_json(output_dir / "countries.geojson", map_document)
    return statistics, map_document


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", type=Path, default=DEFAULT_SOURCE_CSV)
    parser.add_argument(
        "--natural-earth-dbf",
        type=Path,
        default=DEFAULT_NATURAL_EARTH_BASE.with_suffix(".dbf"),
    )
    parser.add_argument(
        "--natural-earth-shp",
        type=Path,
        default=DEFAULT_NATURAL_EARTH_BASE.with_suffix(".shp"),
    )
    parser.add_argument("--zone-tab", type=Path, default=default_zone_tab())
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    statistics, map_document = build(
        arguments.source_csv,
        arguments.natural_earth_dbf,
        arguments.natural_earth_shp,
        arguments.zone_tab,
        arguments.output_dir,
    )
    polygon_count = len(map_document["features"])
    marker_fallbacks = sum(
        country["marker_source"] == "tzdb-zone.tab"
        for country in statistics["countries"]
    )
    print(
        f"Wrote {statistics['totals']['observation_count']} source observations as "
        f"{statistics['totals']['published_exact_cell_count']} exact cells and "
        f"{statistics['totals']['published_group_cell_count']} group cells for "
        f"{statistics['totals']['country_count']} countries; "
        f"{polygon_count} map polygons, {marker_fallbacks} zone.tab markers."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import copy
import csv
import json
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = SITE_ROOT / "MAGENHA_DATA" / "haplogroup_statistics"
sys.path.insert(0, str(SITE_ROOT))

from scripts import build_haplogroup_statistics as builder


def fixture_provenance():
    return {
        "inputs": {
            key: {"file": f"{key}.fixture", "sha256": "0" * 64}
            for key in builder.PROVENANCE_INPUT_KEYS
        },
        "natural_earth": {
            "dataset": "Admin 0 – Countries, 1:110m",
            "version": "fixture",
            "license": "Public domain",
        },
        "coordinate_reference_system": builder.COORDINATE_REFERENCE_SYSTEM,
        "generated_by": "scripts/build_haplogroup_statistics.py",
    }


class AggregationTests(unittest.TestCase):
    def test_csv_rows_are_aggregated_and_group_mismatches_are_rejected(self):
        rows = [
            ("legacy", "YDNA", "R-M269", "CU", "R"),
            ("legacy", "YDNA", "R-M269", "CU", "R"),
            ("legacy", "mtDNA", "H1", "ES", "H"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            csv_path = Path(temporary) / "source.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as destination:
                writer = csv.writer(destination)
                writer.writerow(
                    ["source", "type_haplogroup", "haplogroup", "country", "Group"]
                )
                writer.writerows(rows)
            observations, row_count = builder.read_observations(csv_path)

            self.assertEqual(row_count, 3)
            self.assertEqual(observations[("YDNA", "R-M269", "R", "CU")], 2)

            csv_path.write_text(
                "source,type_haplogroup,haplogroup,country,Group\n"
                "legacy,YDNA,R-M269,CU,E\n",
                encoding="utf-8",
            )
            with self.assertRaises(builder.DataError):
                builder.read_observations(csv_path)

    def test_disclosure_control_and_observation_denominators(self):
        raw = Counter(
            {
                ("YDNA", "R-M269", "R", "CU"): 20,
                ("YDNA", "R-U152", "R", "CU"): 4,
                ("YDNA", "E-M35", "E", "CU"): 6,
                ("YDNA", "Q-M3", "Q", "CU"): 5,
                ("YDNA", "R-M269", "R", "ES"): 25,
                ("YDNA", "E-M35", "E", "ES"): 4,
                ("YDNA", "Q-M3", "Q", "ES"): 5,
                ("mtDNA", "H1", "H", "CU"): 29,
            }
        )
        earth = {
            "CU": {"names": {"en": "Cuba", "es": "Cuba"}, "label": [-79, 21]},
            "ES": {"names": {"en": "Spain", "es": "España"}, "label": [-4, 40]},
        }
        document = builder.build_statistics_document(
            raw,
            sum(raw.values()),
            earth,
            {},
            provenance=fixture_provenance(),
        )
        countries = {country["alpha2"]: country for country in document["countries"]}

        self.assertEqual(
            countries["CU"]["observation_counts"],
            {"YDNA": 35, "mtDNA": 29, "total": 64},
        )
        self.assertEqual(
            document["methodology"]["denominator_key"],
            "countries[].observation_counts[type]",
        )

        exact = {tuple(row[:4]): row[4] for row in document["observations"]}
        groups = {tuple(row[:3]): row[3] for row in document["group_observations"]}
        self.assertEqual(
            exact,
            {
                ("YDNA", "E-M35", "E", "CU"): 6,
                ("YDNA", "Q-M3", "Q", "CU"): 5,
                ("YDNA", "R-M269", "R", "ES"): 25,
            },
        )
        self.assertEqual(
            groups,
            {
                ("YDNA", "E", "CU"): 6,
                ("YDNA", "Q", "CU"): 5,
                ("YDNA", "R", "CU"): 24,
                ("YDNA", "R", "ES"): 25,
            },
        )
        self.assertNotIn("by_source", document["totals"])

    def test_complementary_suppression_never_leaves_one_hidden_child(self):
        raw = Counter(
            {
                ("YDNA", "R-M269", "R", "CU"): 20,
                ("YDNA", "R-U152", "R", "CU"): 4,
                ("YDNA", "E-M35", "E", "CU"): 6,
                ("YDNA", "Q-M3", "Q", "CU"): 5,
                ("YDNA", "R-M269", "R", "ES"): 25,
                ("YDNA", "E-M35", "E", "ES"): 4,
                ("YDNA", "Q-M3", "Q", "ES"): 5,
            }
        )
        denominators = defaultdict(Counter)
        raw_groups = defaultdict(Counter)
        raw_exact = defaultdict(set)
        for (haplogroup_type, haplogroup, group, alpha2), count in raw.items():
            denominators[alpha2][haplogroup_type] += count
            raw_groups[(haplogroup_type, alpha2)][group] += count
            raw_exact[(haplogroup_type, group, alpha2)].add(haplogroup)

        published_exact, published_groups = builder.apply_disclosure_control(
            raw, denominators
        )
        published_group_keys = set(published_groups)
        published_exact_keys = set(published_exact)
        for (haplogroup_type, alpha2), children in raw_groups.items():
            if (
                denominators[alpha2][haplogroup_type]
                < builder.MINIMUM_COUNTRY_TYPE_OBSERVATION_COUNT
            ):
                continue
            visible = {
                group
                for published_type, group, published_alpha2 in published_group_keys
                if published_type == haplogroup_type and published_alpha2 == alpha2
            }
            self.assertNotEqual(len(set(children) - visible), 1)

        for parent in published_group_keys:
            haplogroup_type, group, alpha2 = parent
            visible = {
                haplogroup
                for (
                    published_type,
                    haplogroup,
                    published_group,
                    published_alpha2,
                ) in published_exact_keys
                if (
                    published_type,
                    published_group,
                    published_alpha2,
                )
                == (haplogroup_type, group, alpha2)
            }
            self.assertNotEqual(len(raw_exact[parent] - visible), 1)

    def test_zone_tab_coordinate_formats(self):
        self.assertEqual(builder.parse_zone_coordinate("+4257+00131"), [1.51667, 42.95])
        self.assertEqual(
            builder.parse_zone_coordinate("+404251-0740023"),
            [-74.00639, 40.71417],
        )


class PublishedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.statistics_path = DATA_DIR / "statistics.json"
        cls.map_path = DATA_DIR / "countries.geojson"
        cls.statistics = json.loads(cls.statistics_path.read_text(encoding="utf-8"))
        cls.map_document = json.loads(cls.map_path.read_text(encoding="utf-8"))

    def test_generated_documents_validate(self):
        builder.validate_statistics_document(self.statistics)
        builder.validate_map_document(self.map_document)
        builder.validate_cross_document_coverage(self.statistics, self.map_document)

    def test_every_dataset_code_has_a_marker_denominator_and_metadata(self):
        country_codes = {country["alpha2"] for country in self.statistics["countries"]}
        self.assertEqual(len(country_codes), self.statistics["totals"]["country_count"])
        for country in self.statistics["countries"]:
            self.assertEqual(len(country["marker"]), 2)
            self.assertTrue(country["names"]["en"])
            self.assertTrue(country["names"]["es"])
            self.assertGreater(country["observation_counts"]["total"], 0)

    def test_stable_natural_earth_iso2_fixes_are_present(self):
        map_codes = {
            feature["properties"]["alpha2"] for feature in self.map_document["features"]
        }
        self.assertTrue({"FR", "NO", "TW", "XK"}.issubset(map_codes))
        self.assertNotIn("-99", map_codes)

    def test_totals_match_retained_denominators(self):
        counts_by_type = Counter()
        for country in self.statistics["countries"]:
            for haplogroup_type in self.statistics["types"]:
                counts_by_type[haplogroup_type] += country["observation_counts"][
                    haplogroup_type
                ]
        self.assertEqual(
            sum(counts_by_type.values()),
            self.statistics["totals"]["observation_count"],
        )
        self.assertEqual(dict(counts_by_type), self.statistics["totals"]["by_type"])

    def test_every_published_cell_meets_disclosure_thresholds(self):
        countries = {
            country["alpha2"]: country for country in self.statistics["countries"]
        }
        group_keys = {
            (haplogroup_type, group, alpha2)
            for haplogroup_type, group, alpha2, _count in self.statistics[
                "group_observations"
            ]
        }
        for haplogroup_type, _group, alpha2, count in self.statistics[
            "group_observations"
        ]:
            self.assertGreaterEqual(count, builder.MINIMUM_CELL_COUNT)
            self.assertGreaterEqual(
                countries[alpha2]["observation_counts"][haplogroup_type],
                builder.MINIMUM_COUNTRY_TYPE_OBSERVATION_COUNT,
            )
        for haplogroup_type, _haplogroup, group, alpha2, count in self.statistics[
            "observations"
        ]:
            self.assertGreaterEqual(count, builder.MINIMUM_CELL_COUNT)
            self.assertIn((haplogroup_type, group, alpha2), group_keys)

    def test_indexes_contain_only_values_with_published_cells(self):
        expected_haplogroups = {
            haplogroup_type: sorted(
                {
                    row[1]
                    for row in self.statistics["observations"]
                    if row[0] == haplogroup_type
                },
                key=lambda value: (value.casefold(), value),
            )
            for haplogroup_type in self.statistics["types"]
        }
        expected_groups = {
            haplogroup_type: sorted(
                {
                    row[1]
                    for row in self.statistics["group_observations"]
                    if row[0] == haplogroup_type
                },
                key=lambda value: (value.casefold(), value),
            )
            for haplogroup_type in self.statistics["types"]
        }
        self.assertEqual(self.statistics["haplogroups"], expected_haplogroups)
        self.assertEqual(self.statistics["groups"], expected_groups)

    def test_provenance_has_all_hashes_without_raw_source_name(self):
        inputs = self.statistics["provenance"]["inputs"]
        self.assertEqual(set(inputs), set(builder.PROVENANCE_INPUT_KEYS))
        self.assertEqual(inputs["source_csv"]["file"], "private-source.csv")
        self.assertNotIn("23andmestatistics", self.statistics_path.read_text())
        for value in inputs.values():
            self.assertRegex(value["sha256"], r"^[0-9a-f]{64}$")
        self.assertNotIn("by_source", self.statistics["totals"])

    def test_artifact_validators_reject_corruption(self):
        statistics = copy.deepcopy(self.statistics)
        statistics["totals"]["country_count"] += 1
        with self.assertRaises(builder.DataError):
            builder.validate_statistics_document(statistics)

        map_document = copy.deepcopy(self.map_document)
        map_document["features"][0]["geometry"]["coordinates"] = []
        with self.assertRaises(builder.DataError):
            builder.validate_map_document(map_document)

    def test_published_data_directory_has_exact_recursive_allowlist(self):
        self.assertFalse(any(path.is_symlink() for path in DATA_DIR.rglob("*")))
        published = sorted(
            path.relative_to(DATA_DIR).as_posix()
            for path in DATA_DIR.rglob("*")
            if path.is_file()
        )
        self.assertEqual(
            published,
            ["README.md", "countries.geojson", "statistics.json"],
        )

    def test_committed_artifacts_regenerate_byte_for_byte_when_inputs_exist(self):
        inputs = (
            builder.DEFAULT_SOURCE_CSV,
            builder.DEFAULT_NATURAL_EARTH_BASE.with_suffix(".dbf"),
            builder.DEFAULT_NATURAL_EARTH_BASE.with_suffix(".shp"),
            builder.default_zone_tab(),
        )
        if not all(path.is_file() for path in inputs):
            self.skipTest(
                "private/unified-workspace regeneration inputs are unavailable"
            )
        with tempfile.TemporaryDirectory() as temporary:
            builder.build(*inputs, Path(temporary))
            self.assertEqual(
                self.statistics_path.read_bytes(),
                (Path(temporary) / "statistics.json").read_bytes(),
            )
            self.assertEqual(
                self.map_path.read_bytes(),
                (Path(temporary) / "countries.geojson").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()

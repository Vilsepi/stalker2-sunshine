#!/usr/bin/env python3
"""Tests for the weather patcher. Tests that need the original game config are skipped if it's missing."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import yaml  # noqa: E402

from cfg_parser import Struct, format_value, load_weather_selections, merge, parse_cfg_text, parse_value  # noqa: E402
from cfg_patcher import build_variant, diff_weathers, generate_bpatch  # noqa: E402
from cfg_to_yml import DEFAULT_CFG, DEFAULT_OUTPUT, generate_yml  # noqa: E402

CONFIG_DIR = REPO_ROOT / "src" / "config"
HAS_ORIGINAL = DEFAULT_CFG.is_file()


def load_yaml(name: str) -> dict:
    return yaml.safe_load((CONFIG_DIR / name).read_text()) or {}


def apply_bpatch(original: dict[str, Struct], patch_text: str) -> dict[str, Struct]:
    """Simulate the game applying a bpatch file. Fails on keys that don't exist in the original."""
    result = dict(original)
    for patch in parse_cfg_text(patch_text):
        assert patch.options == "bpatch", f"{patch.key} is missing {{bpatch}}"
        assert patch.key in original, f"Unknown SID {patch.key}"
        for weather_name, weather in patch.structs().items():
            assert weather.options == "bpatch", f"{patch.key}.{weather_name} is missing {{bpatch}}"
            target = original[patch.key].structs()
            assert weather_name in target, f"Unknown weather {patch.key}.{weather_name}"
            for param in weather.items:
                assert param in target[weather_name].items, f"Unknown param {patch.key}.{weather_name}.{param}"
        result[patch.key] = merge(original[patch.key], patch)
    return result


class TestValues(unittest.TestCase):
    def test_parse_value(self):
        self.assertEqual(parse_value("30.f"), 30.0)
        self.assertEqual(parse_value("20.0"), 20.0)
        self.assertEqual(parse_value("1.5f"), 1.5)
        self.assertEqual(parse_value("1"), 1)
        self.assertIsInstance(parse_value("1"), int)
        self.assertIs(parse_value("true"), True)
        self.assertEqual(parse_value("Emission_E15_MQ02"), "Emission_E15_MQ02")

    def test_format_value(self):
        self.assertEqual(format_value(45.0), "45.f")
        self.assertEqual(format_value(12.5), "12.5f")
        self.assertEqual(format_value(2), "2")
        self.assertEqual(format_value(False), "false")


class TestVariant(unittest.TestCase):
    def setUp(self):
        self.vanilla = load_yaml("vanilla.yml")

    def test_empty_variant_produces_no_changes(self):
        variant = build_variant(self.vanilla, {})
        self.assertEqual(diff_weathers(self.vanilla, variant), {})

    def test_overrides_only_change_given_values(self):
        variant = build_variant(self.vanilla, load_yaml("test.yml"))
        changes = diff_weathers(self.vanilla, variant)
        self.assertEqual(changes["RostokWeatherSelection"], {
            "Clearly": {"BlendWeight": 45.0},
            "LightRainy": {"BlendWeight": 15.0},
        })
        self.assertEqual(set(changes), {"YanovWeatherSelection", "RostokWeatherSelection"})

    def test_excluded_regions_are_unchanged(self):
        variant_config = load_yaml("sunnier.yml")
        changes = diff_weathers(self.vanilla, build_variant(self.vanilla, variant_config))
        for sid in variant_config.get("exclude", []):
            self.assertNotIn(sid, changes)

    def test_unknown_region_is_rejected(self):
        with self.assertRaises(ValueError):
            build_variant(self.vanilla, {"overrides": {"NoSuchRegion": {"Clearly": {"BlendWeight": 1.0}}}})

    def test_single_weather_regions_are_unchanged(self):
        vanilla = {
            "Forced": {"Rainy": {"BlendWeight": 100.0}, "Clearly": {"BlendWeight": 0.0}},
            "Mixed": {"Rainy": {"BlendWeight": 50.0}, "Clearly": {"BlendWeight": 50.0}},
        }
        variant = build_variant(vanilla, {"multipliers": {"Rainy": 0.5, "Clearly": 2.0}})
        self.assertEqual(diff_weathers(vanilla, variant), {
            "Mixed": {"Rainy": {"BlendWeight": 25.0}, "Clearly": {"BlendWeight": 100.0}},
        })
        with self.assertRaises(ValueError):
            build_variant(vanilla, {"overrides": {"Forced": {"Rainy": {"BlendWeight": 1.0}}}})

    def test_override_of_excluded_region_is_rejected(self):
        with self.assertRaises(ValueError):
            build_variant(self.vanilla, {"exclude": ["Empty"], "overrides": {"Empty": {"Clearly": {"BlendWeight": 1.0}}}})

    def test_sunnier_increases_clear_weather_everywhere(self):
        variant_config = load_yaml("sunnier.yml")
        variant = build_variant(self.vanilla, variant_config)
        for sid, weathers in variant.items():
            if sid in variant_config.get("exclude", []):
                continue
            total_before = sum(w["BlendWeight"] for w in self.vanilla[sid].values())
            total_after = sum(w["BlendWeight"] for w in weathers.values())
            share_before = self.vanilla[sid]["Clearly"]["BlendWeight"] / total_before
            share_after = weathers["Clearly"]["BlendWeight"] / total_after
            self.assertGreater(share_after, share_before, sid)


@unittest.skipUnless(HAS_ORIGINAL, f"Original game config not found: {DEFAULT_CFG}")
class TestAgainstOriginal(unittest.TestCase):
    def setUp(self):
        self.original = load_weather_selections(DEFAULT_CFG)
        self.vanilla = load_yaml("vanilla.yml")

    def test_parses_all_regions(self):
        self.assertEqual(len(self.original), 45)
        for sid, region in self.original.items():
            self.assertIn("Clearly", region.structs(), sid)

    def test_vanilla_yml_is_up_to_date(self):
        self.assertEqual(DEFAULT_OUTPUT.read_text(), generate_yml(DEFAULT_CFG),
                         "vanilla.yml is out of date, run: python3 src/cfg_to_yml.py")

    def test_sunnier_bpatch_applies_to_original(self):
        variant = build_variant(self.vanilla, load_yaml("sunnier.yml"))
        patch_text = generate_bpatch(diff_weathers(self.vanilla, variant))
        patched = apply_bpatch(self.original, patch_text)

        for sid, weathers in variant.items():
            region = patched[sid].structs()
            for weather_name, params in weathers.items():
                for param, value in params.items():
                    self.assertEqual(region[weather_name].items[param], value, f"{sid}.{weather_name}.{param}")
            total = sum(w.items["BlendWeight"] for w in region.values())
            self.assertGreater(total, 0, sid)

    def test_bpatch_only_contains_changed_values(self):
        variant = build_variant(self.vanilla, load_yaml("test.yml"))
        patch_text = generate_bpatch(diff_weathers(self.vanilla, variant))
        patched = apply_bpatch(self.original, patch_text)
        for sid in set(self.original) - {"YanovWeatherSelection", "RostokWeatherSelection"}:
            self.assertIs(patched[sid], self.original[sid])


if __name__ == "__main__":
    unittest.main()

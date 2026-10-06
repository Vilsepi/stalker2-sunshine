#!/usr/bin/env python3
"""Unit tests that don't need the original game config files."""

import unittest

from helpers import load_yaml

from cfg_parser import format_value, parse_cfg_text, parse_value
from cfg_patcher import build_variant, diff_weathers, generate_bpatch


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


class TestParser(unittest.TestCase):
    def test_parses_any_param_order_and_inheritance(self):
        roots = parse_cfg_text(
            "[0] : struct.begin\n"
            "   SID = Base\n"
            "   Clearly : struct.begin\n"
            "      BlendWeight = 40.f\n"
            "      MaximumRepeatAmount = 1\n"
            "   struct.end\n"
            "struct.end\n"
            "Child : struct.begin {refkey=[0]}\n"
            "   Clearly : struct.begin\n"
            "      MaximumRepeatAmount = 2\n"
            "      BlendWeight = 20.0\n"
            "   struct.end\n"
            "   SID = Child\n"
            "   Priority = 5\n"
            "struct.end\n"
        )
        self.assertEqual([r.sid for r in roots], ["Base", "Child"])
        self.assertEqual(roots[1].refkey, "[0]")
        self.assertEqual(roots[1].items["Priority"], 5)
        self.assertEqual(roots[1].structs()["Clearly"].items, {"MaximumRepeatAmount": 2, "BlendWeight": 20.0})

    def test_rejects_unknown_syntax(self):
        with self.assertRaises(ValueError):
            parse_cfg_text("Foo : struct.begin\n   not valid\nstruct.end\n")
        with self.assertRaises(ValueError):
            parse_cfg_text("Foo : struct.begin\n")


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


class TestBpatch(unittest.TestCase):
    def test_sunnier_bpatch_syntax(self):
        vanilla = load_yaml("vanilla.yml")
        changes = diff_weathers(vanilla, build_variant(vanilla, load_yaml("sunnier.yml")))
        patches = parse_cfg_text(generate_bpatch(changes))

        self.assertEqual([p.key for p in patches], list(changes))
        for patch in patches:
            self.assertEqual(patch.options, "bpatch", patch.key)
            for weather_name, weather in patch.structs().items():
                self.assertEqual(weather.options, "bpatch", f"{patch.key}.{weather_name}")
                self.assertEqual(weather.items, changes[patch.key][weather_name])


if __name__ == "__main__":
    unittest.main()

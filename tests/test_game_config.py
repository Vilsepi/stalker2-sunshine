#!/usr/bin/env python3
"""Tests against the original game config files. Skipped if they are missing (see README)."""

import unittest

from helpers import CONFIG_DIR, load_yaml

from cfg_parser import Struct, load_weather_selections, merge, parse_cfg_text
from cfg_patcher import build_variant, diff_weathers, generate_bpatch
from cfg_to_yml import DEFAULT_CFG, DEFAULT_OUTPUT, generate_yml


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


@unittest.skipUnless(DEFAULT_CFG.is_file(), f"Original game config not found: {DEFAULT_CFG}")
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

    def test_variant_bpatches_apply_to_original(self):
        for variant_file in sorted(CONFIG_DIR.glob("*.yml")):
            if variant_file.name == "vanilla.yml":
                continue
            with self.subTest(variant=variant_file.name):
                variant = build_variant(self.vanilla, load_yaml(variant_file.name))
                patch_text = generate_bpatch(diff_weathers(self.vanilla, variant))
                patched = apply_bpatch(self.original, patch_text)

                for sid, weathers in variant.items():
                    region = patched[sid].structs()
                    for weather_name, params in weathers.items():
                        for param, value in params.items():
                            self.assertEqual(region[weather_name].items[param], value, f"{sid}.{weather_name}.{param}")
                    total = sum(w.items["BlendWeight"] for w in region.values())
                    self.assertGreater(total, 0, sid)

    def test_bpatch_only_changes_patched_values(self):
        changes = diff_weathers(self.vanilla, build_variant(self.vanilla, load_yaml("sunnier.yml")))
        patched = apply_bpatch(self.original, generate_bpatch(changes))

        for sid, original in self.original.items():
            if sid not in changes:
                self.assertIs(patched[sid], original, sid)
                continue
            for weather_name, weather in original.structs().items():
                patched_params = changes[sid].get(weather_name, {})
                for param, value in weather.items.items():
                    if param not in patched_params:
                        self.assertEqual(patched[sid].structs()[weather_name].items[param], value,
                                         f"{sid}.{weather_name}.{param}")

if __name__ == "__main__":
    unittest.main()

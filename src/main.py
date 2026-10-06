#!/usr/bin/env python3
"""
STALKER 2 Weather Config Patcher

Builds a weather variant on top of vanilla.yml and writes it as a bpatch file
into the mod's directory structure, ready to be packed with repak.

Usage: python3 main.py <variant.yml>
"""

import argparse
import shutil
import sys
from pathlib import Path

import yaml

from cfg_patcher import build_variant, diff_weathers, generate_bpatch, write_cfg
from cfg_to_yml import REGIONS

# Available parameters:
#   BlendWeight (float): Selection probability weight
#   WeatherDurationMin (float): Minimum duration in seconds
#   WeatherDurationMax (float): Maximum duration in seconds
#   MaximumRepeatAmount (int): Max consecutive occurrences
#   MaximumCooldownWeatherAmount (int): Cooldown in weather cycles

SRC_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SRC_DIR / "config"
DIST_DIR = SRC_DIR.parent / "dist"
MOD_NAME = "Sunshine"
PATCH_PATH = Path("Stalker2/Content/GameLite/GameData/WeatherSelectionPrototypes") / f"WeatherSelectionPrototypes_patch_{MOD_NAME}.cfg"

TABLE_WEATHERS = ["Clearly", "Cloudy", "Fogy", "Stormy", "LightRainy", "Rainy"]


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def shares(weathers: dict) -> dict[str, float]:
    """Selection probability (%) of each weather type, from BlendWeights."""
    weights = {w: weathers.get(w, {}).get("BlendWeight", 0) for w in TABLE_WEATHERS}
    total = sum(weights.values())
    return {w: 100 * v / total if total else 0 for w, v in weights.items()}


def region_label(sid: str) -> str:
    """Area description followed by the region's SID, e.g. "Cordon (KordonWeatherSelection)"."""
    return f"{REGIONS[sid]} ({sid})" if sid in REGIONS else sid


def print_table(vanilla: dict, variant: dict) -> None:
    """Print selection probabilities per region, vanilla -> variant."""
    width = max(len(region_label(sid)) for sid in vanilla) + 2
    print(f"\n{'Selection chance %, vanilla -> variant':{width}}" + "".join(f"{w:>12}" for w in TABLE_WEATHERS))
    for sid in vanilla:
        before, after = shares(vanilla[sid]), shares(variant[sid])
        cells = "".join(
            f"{before[w]:>5.0f} ->{after[w]:>3.0f}" if before[w] != after[w] else f"{before[w]:>12.0f}"
            for w in TABLE_WEATHERS
        )
        print(f"{region_label(sid):{width}}{cells}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a bpatch weather mod for STALKER 2")
    parser.add_argument("variant_file", help="Variant YAML file: a path, or a name in src/config (e.g. sunnier.yml)")
    args = parser.parse_args()

    variant_path = Path(args.variant_file)
    if not variant_path.is_file():
        variant_path = CONFIG_DIR / args.variant_file
    if not variant_path.is_file():
        print(f"Error: Variant file not found: {args.variant_file} (also looked in {CONFIG_DIR})")
        sys.exit(1)

    vanilla = load_yaml(CONFIG_DIR / "vanilla.yml")
    variant = build_variant(vanilla, load_yaml(variant_path))
    changes = diff_weathers(vanilla, variant)

    mod_dir = DIST_DIR / f"{MOD_NAME}_P"
    shutil.rmtree(mod_dir, ignore_errors=True)
    output_path = mod_dir / PATCH_PATH
    write_cfg(generate_bpatch(changes), output_path)

    print_table(vanilla, variant)
    print(f"\nPatched {len(changes)} regions")
    print(f"Output saved to: {output_path}")

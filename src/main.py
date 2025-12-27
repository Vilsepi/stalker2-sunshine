#!/usr/bin/env python3
"""
STALKER 2 Weather Config Patcher

Main entry point for generating patched weather configuration files.
Usage: python main.py <patch_file.json>
"""

import argparse
import json
import sys
from pathlib import Path

from cfg_patcher import patch_and_generate

# Available parameters:
#   BlendWeight (float): Selection probability weight
#   BlendWeightIncrease (float): Weight increase over time
#   WeatherDurationMin (float): Minimum duration in seconds
#   WeatherDurationMax (float): Maximum duration in seconds
#   MaximumRepeatAmount (int): Max consecutive occurrences (-1 = unlimited)
#   MaximumCooldownWeatherAmount (int): Cooldown in weather cycles


def load_patch_from_json(json_path: Path) -> dict:
    """
    Load patch configuration from a JSON file.

    Args:
        json_path: Path to the JSON file

    Returns:
        Patch configuration dictionary
    """
    with open(json_path) as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate patched weather configuration files for STALKER 2"
    )
    parser.add_argument(
        "patch_file",
        help="Name of the patch JSON file in the config directory (e.g., patches.json)",
    )
    args = parser.parse_args()

    src_dir = Path(__file__).parent
    repo_root = src_dir.parent
    original_dir = repo_root / "original_config_chunked"
    output_path = repo_root / "dist" / "output.cfg"
    patch_json = src_dir / "config" / args.patch_file

    if not patch_json.exists():
        print(f"Error: Patch file not found: {patch_json}")
        sys.exit(1)

    patch_config = load_patch_from_json(patch_json)
    result = patch_and_generate(original_dir, patch_config, output_path)

    print(f"\nGenerated {len(result.splitlines())} lines of config")
    print(f"Output saved to: {output_path}")

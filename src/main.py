#!/usr/bin/env python3
"""
STALKER 2 Weather Config Patcher

Main entry point for generating patched weather configuration files.
Edit the PATCH_CONFIG below to customize weather settings.
"""

import json
import sys
from pathlib import Path

from cfg_patcher import patch_and_generate

#
# Structure:
# - "skip_files": List of .cfg files to leave completely unchanged
# - "configs": Dict of SID -> patch settings
#   - "skip_weathers": Weather types to leave unchanged within this config
#   - "weathers": Dict of weather_type -> parameters to patch
#
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
    """Alternative entry point using JSON patch file."""
    src_dir = Path(__file__).parent
    original_dir = src_dir / "config" / "original_chunked"
    output_path = src_dir / "config" / "patched_combined.cfg"
    patch_json = src_dir / "patches.json"

    if not patch_json.exists():
        print(f"Error: Patch file not found: {patch_json}")
        print("Create patches.json or use main() with inline PATCH_CONFIG")
        sys.exit(1)

    patch_config = load_patch_from_json(patch_json)
    result = patch_and_generate(original_dir, patch_config, output_path)

    print(f"\nGenerated {len(result.splitlines())} lines of config")
    print(f"Output saved to: {output_path}")

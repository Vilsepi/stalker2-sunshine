#!/usr/bin/env python3
"""
STALKER 2 Weather Config Patcher

Main entry point for generating patched weather configuration files.
Usage: python main.py <patch_file.yml>
"""

import argparse
import sys
from pathlib import Path
import yaml

from cfg_patcher import patch_and_generate

# Available parameters:
#   BlendWeight (float): Selection probability weight
#   BlendWeightIncrease (float): Weight increase over time
#   WeatherDurationMin (float): Minimum duration in seconds
#   WeatherDurationMax (float): Maximum duration in seconds
#   MaximumRepeatAmount (int): Max consecutive occurrences (-1 = unlimited)
#   MaximumCooldownWeatherAmount (int): Cooldown in weather cycles


def load_patch_from_yaml(yaml_path: Path) -> dict:
    """
    Load patch configuration from a YAML file.

    Args:
        yaml_path: Path to the YAML file

    Returns:
        Patch configuration dictionary
    """
    with open(yaml_path) as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate patched weather configuration files for STALKER 2"
    )
    parser.add_argument(
        "patch_file",
        help="Name of the patch YAML file in the config directory (e.g., patches.yml)",
    )
    args = parser.parse_args()

    src_dir = Path(__file__).parent
    repo_root = src_dir.parent
    original_dir = repo_root / "original_config_chunked"
    output_path = repo_root / "dist" / "output.cfg"
    patch_yaml = src_dir / "config" / args.patch_file

    if not patch_yaml.exists():
        print(f"Error: Patch file not found: {patch_yaml}")
        sys.exit(1)

    patch_config = load_patch_from_yaml(patch_yaml)
    result = patch_and_generate(original_dir, patch_config, output_path)

    print(f"\nGenerated {len(result.splitlines())} lines of config")
    print(f"Output saved to: {output_path}")

#!/usr/bin/env python3
"""
Config patcher for STALKER 2 weather configuration files.
Applies patches from a dict/JSON structure to original configs.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cfg_parser import ConfigData, WeatherTypeData, format_value, parse_all_configs


@dataclass
class PatchConfig:
    """
    Configuration for patching weather configs.

    Patch format - simple SID -> weather -> params mapping:
    {
        "VortexWeatherSelection": {
            "Clearly": {
                "BlendWeight": 80.0,
                "WeatherDurationMin": 800.0
            },
            "Cloudy": {
                "BlendWeight": 20.0
            }
        }
    }

    Only the specified weather types and params are modified.
    Everything else (files, weather types, params) stays unchanged.
    """
    configs: dict[str, dict[str, dict[str, Any]]]

    @classmethod
    def from_dict(cls, data: dict) -> "PatchConfig":
        """Create PatchConfig from a dictionary."""
        return cls(configs=data)


def generate_config_output(config: ConfigData) -> str:
    """
    Generate the .cfg file content from a ConfigData object.

    Args:
        config: The config data to generate output for

    Returns:
        String content of the .cfg file
    """
    lines = []

    # Header line
    if config.refkey:
        lines.append(f"{config.config_id} : struct.begin {{refkey={config.refkey}}}")
    else:
        lines.append(f"{config.config_id} : struct.begin")

    # SID
    lines.append(f"   SID = {config.sid}")

    # Priority (only if it exists in original)
    if config.priority is not None:
        lines.append(f"   Priority = {config.priority}")

    # Extra params (e.g., EmissionPrototypeSID)
    for param_name, param_value in config.extra_params.items():
        lines.append(f"   {param_name} = {param_value}")

    # Weather types in original order
    for weather_name in config.weather_order:
        weather = config.weather_types[weather_name]

        # Handle slight formatting variation: "Underground:" vs "Underground :"
        if weather_name == "Underground":
            lines.append(f"   {weather_name}: struct.begin")
        else:
            lines.append(f"   {weather_name} : struct.begin")

        # Parameters in standard order
        for param_name in WeatherTypeData.PARAM_ORDER:
            if param_name in weather.params:
                value = format_value(weather.params[param_name])
                lines.append(f"      {param_name} = {value}")

        lines.append("   struct.end")

    # Footer
    lines.append("struct.end")

    return "\n".join(lines)


def apply_patches(
    configs: list[ConfigData],
    patch_config: PatchConfig,
) -> list[ConfigData]:
    """
    Apply patches to a list of configs.

    Args:
        configs: List of original ConfigData objects
        patch_config: The patch configuration to apply

    Returns:
        List of patched ConfigData objects (copies, originals unchanged)
    """
    import copy

    patched_configs = []

    for config in configs:
        # Check if there are patches for this config's SID
        if config.sid not in patch_config.configs:
            patched_configs.append(config)
            continue

        # Deep copy to avoid modifying original
        patched = copy.deepcopy(config)
        weather_patches = patch_config.configs[config.sid]

        # Apply patches to specified weather types
        for weather_name, param_patches in weather_patches.items():
            if weather_name in patched.weather_types:
                for param_name, param_value in param_patches.items():
                    patched.weather_types[weather_name].params[param_name] = param_value

        patched_configs.append(patched)

    return patched_configs


def generate_combined_config(configs: list[ConfigData]) -> str:
    """
    Generate the combined .cfg file from all configs.

    Args:
        configs: List of ConfigData objects in order

    Returns:
        Combined config file content
    """
    parts = []
    for config in configs:
        parts.append(generate_config_output(config))

    return "\n".join(parts)


def patch_and_generate(
    original_dir: Path,
    patch_data: dict,
    output_path: Path | None = None,
) -> str:
    """
    Main function: parse originals, apply patches, generate output.

    Args:
        original_dir: Path to directory with original .cfg files
        patch_data: Dictionary with patch configuration
        output_path: Optional path to write output file (with CRLF)

    Returns:
        Combined config file content
    """
    # Parse all original configs
    configs = parse_all_configs(original_dir)

    # Create patch config
    patch_config = PatchConfig.from_dict(patch_data)

    # Apply patches
    patched_configs = apply_patches(configs, patch_config)

    # Generate combined output
    combined = generate_combined_config(patched_configs)

    # Write to file if path provided
    if output_path:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Convert to CRLF line endings for the game and add trailing newline
        combined_crlf = combined.replace("\n", "\r\n") + "\r\n"
        # Write with UTF-8 BOM to match original file
        output_path.write_bytes(b'\xef\xbb\xbf' + combined_crlf.encode('utf-8'))
        print(f"Output written to {output_path}")

    return combined

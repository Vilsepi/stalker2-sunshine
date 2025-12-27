#!/usr/bin/env python3
"""
Generates a YAML config from STALKER 2 .cfg weather configuration files.
Uses cfg_parser to read the files and outputs a filtered subset of parameters.
"""

import sys
from pathlib import Path

import yaml

from cfg_parser import parse_all_configs, ConfigData


# Weather types to include in output
INCLUDED_WEATHERS = {"Clearly", "Cloudy", "Stormy", "LightRainy", "Rainy"}

# Parameters to include in output (in order)
INCLUDED_PARAMS = [
    "BlendWeight",
    "WeatherDurationMin",
    "WeatherDurationMax",
    "MaximumRepeatAmount",
    "MaximumCooldownWeatherAmount",
]


def config_to_dict(config: ConfigData) -> dict | None:
    """
    Convert a ConfigData object to a filtered dictionary for YAML output.

    Returns None if no weather types pass the filter.
    """
    weather_dict = {}

    for weather_name in config.weather_order:
        # Skip weather types not in our include list
        if weather_name not in INCLUDED_WEATHERS:
            continue

        weather_data = config.weather_types[weather_name]

        # Skip if BlendWeight is 0
        blend_weight = weather_data.params.get("BlendWeight", 0)
        if blend_weight == 0 or blend_weight == 0.0:
            continue

        # Build filtered params dict
        params = {}
        for param_name in INCLUDED_PARAMS:
            if param_name not in weather_data.params:
                continue

            value = weather_data.params[param_name]

            # Skip MaximumCooldownWeatherAmount if it's 0
            if param_name == "MaximumCooldownWeatherAmount" and value == 0:
                continue

            params[param_name] = value

        if params:
            weather_dict[weather_name] = params

    return weather_dict if weather_dict else None


def generate_yml(config_dir: Path) -> str:
    """
    Generate YAML content from all .cfg files in the given directory.

    Args:
        config_dir: Path to directory containing .cfg files

    Returns:
        YAML formatted string
    """
    configs = parse_all_configs(config_dir)

    output = {}
    for config in configs:
        config_dict = config_to_dict(config)
        if config_dict:
            output[config.sid] = config_dict

    # Use default_flow_style=False for readable multi-line output
    return yaml.dump(output, default_flow_style=False, sort_keys=False, allow_unicode=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python cfg_to_yml.py <config_directory> [output_file]")
        print("Example: python cfg_to_yml.py ../original_config_chunked output.yml")
        sys.exit(1)

    config_dir = Path(sys.argv[1])

    if not config_dir.is_dir():
        print(f"Error: {config_dir} is not a directory")
        sys.exit(1)

    yml_content = generate_yml(config_dir)

    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
        output_file.write_text(yml_content)
        print(f"Written to {output_file}")
    else:
        print(yml_content)


if __name__ == "__main__":
    main()

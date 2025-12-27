#!/usr/bin/env python3
"""
Parser for STALKER 2 weather configuration files.
Reads .cfg files and extracts structured data.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WeatherTypeData:
    """Represents a single weather type with all its parameters."""
    name: str
    params: dict[str, Any] = field(default_factory=dict)

    # Parameter order matters for output
    PARAM_ORDER = [
        "BlendWeight",
        "BlendWeightIncrease",
        "WeatherDurationMin",
        "WeatherDurationMax",
        "MaximumRepeatAmount",
        "MaximumCooldownWeatherAmount",
        "bAllowInDialogueTransition",
    ]


@dataclass
class ConfigData:
    """Represents a complete weather selection config."""
    filename: str
    config_id: str  # Can be numeric "[0]" or named "SwampWeatherSelection"
    refkey: str | None  # e.g., "[0]" or "[1]"
    sid: str
    priority: int | None = None  # None means Priority field doesn't exist in original
    weather_types: dict[str, WeatherTypeData] = field(default_factory=dict)
    extra_params: dict[str, str] = field(default_factory=dict)  # e.g., EmissionPrototypeSID
    weather_order: list[str] = field(default_factory=list)  # Preserve original order


def parse_value(value_str: str) -> Any:
    """Parse a config value string into the appropriate Python type."""
    value_str = value_str.strip()

    # Boolean
    if value_str == "true":
        return True
    if value_str == "false":
        return False

    # Float with .f suffix
    if value_str.endswith(".f"):
        return float(value_str[:-1])

    # Integer
    try:
        return int(value_str)
    except ValueError:
        pass

    # String (keep as-is)
    return value_str


def format_value(value: Any) -> str:
    """Format a Python value back to config file format."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        # Format with .f suffix, using appropriate decimal places
        if value == int(value):
            return f"{int(value)}.f"
        else:
            return f"{value}f"
    if isinstance(value, int):
        return str(value)
    return str(value)


def parse_cfg_file(filepath: Path) -> ConfigData:
    """
    Parse a single .cfg file and return structured data.

    Args:
        filepath: Path to the .cfg file

    Returns:
        ConfigData object with all parsed information
    """
    content = filepath.read_text(encoding='utf-8-sig')  # Handle BOM
    lines = content.strip().split("\n")

    config_id = ""
    refkey = None
    sid = ""
    priority: int | None = None
    weather_types: dict[str, WeatherTypeData] = {}
    extra_params: dict[str, str] = {}
    weather_order: list[str] = []

    current_weather: WeatherTypeData | None = None
    in_weather_block = False

    for line in lines:
        line = line.rstrip()

        # Skip empty lines
        if not line.strip():
            continue

        # Parse header line: "[0] : struct.begin" or "[1] : struct.begin {refkey=[0]}"
        # or "SwampWeatherSelection : struct.begin {refkey=[1]}"
        header_match = re.match(r'^(\[?\w+\]?)\s*:\s*struct\.begin(?:\s*\{refkey=(\[\d+\])\})?', line)
        if header_match:
            config_id = header_match.group(1)
            refkey = header_match.group(2)  # Will be None if no refkey
            continue

        # Parse top-level struct.end
        if line.strip() == "struct.end" and not in_weather_block:
            continue

        # Parse weather type start: "   Clearly : struct.begin" or "   Underground: struct.begin"
        weather_start_match = re.match(r'^\s+(\w+)\s*:\s*struct\.begin', line)
        if weather_start_match and not in_weather_block:
            weather_name = weather_start_match.group(1)
            current_weather = WeatherTypeData(name=weather_name)
            in_weather_block = True
            continue

        # Parse struct.end for weather block
        if "struct.end" in line and in_weather_block:
            if current_weather:
                weather_types[current_weather.name] = current_weather
                weather_order.append(current_weather.name)
            current_weather = None
            in_weather_block = False
            continue

        # Parse parameter inside weather block
        if in_weather_block and current_weather:
            param_match = re.match(r'^\s+(\w+)\s*=\s*(.+)$', line)
            if param_match:
                param_name = param_match.group(1)
                param_value = parse_value(param_match.group(2))
                current_weather.params[param_name] = param_value
            continue

        # Parse top-level parameters (SID, Priority, EmissionPrototypeSID, etc.)
        top_param_match = re.match(r'^\s+(\w+)\s*=\s*(.+)$', line)
        if top_param_match:
            param_name = top_param_match.group(1)
            param_value = top_param_match.group(2).strip()

            if param_name == "SID":
                sid = param_value
            elif param_name == "Priority":
                priority = int(param_value)
            else:
                extra_params[param_name] = param_value

    return ConfigData(
        filename=filepath.name,
        config_id=config_id,
        refkey=refkey,
        sid=sid,
        priority=priority,
        weather_types=weather_types,
        extra_params=extra_params,
        weather_order=weather_order,
    )


def parse_all_configs(config_dir: Path) -> list[ConfigData]:
    """
    Parse all .cfg files in a directory, sorted by filename.

    Args:
        config_dir: Path to directory containing .cfg files

    Returns:
        List of ConfigData objects, sorted by filename
    """
    cfg_files = sorted(config_dir.glob("*.cfg"))
    return [parse_cfg_file(f) for f in cfg_files]

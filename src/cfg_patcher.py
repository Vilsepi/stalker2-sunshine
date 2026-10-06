#!/usr/bin/env python3
"""
Builds weather variants from vanilla.yml and writes them as a bpatch .cfg file.

Variant format (YAML):

    multipliers:          # BlendWeight multiplier per weather type, applied to every region
      Clearly: 1.5
      Fogy: 0.5
    round_to: 1           # Round multiplied weights to this step (optional)
    exclude:              # Regions left at vanilla values (optional)
      - VortexWeatherSelection
    overrides:            # Exact values, applied after multipliers (optional)
      SwampWeatherSelection:
        Clearly:
          BlendWeight: 40.0

Regions where a single weather type has all the weight (e.g. forced story weather)
are never changed.

The bpatch file only contains values that differ from vanilla, so the game keeps
everything else from its own WeatherSelectionPrototypes.cfg.
"""

import copy
import math
from pathlib import Path
from typing import Any

from cfg_parser import format_value

Weathers = dict[str, dict[str, dict[str, Any]]]  # SID -> weather -> param -> value


def round_weight(original: float, value: float, step: float | None) -> float:
    """Round to the nearest step, but never round a non-zero weight down to zero."""
    if not step:
        return float(value)
    rounded = math.floor(value / step + 0.5) * step
    if rounded == 0 and original > 0 and value > 0:
        rounded = step
    return float(rounded)


def is_single_weather(weathers: dict[str, dict[str, Any]]) -> bool:
    """True if only one weather type has a non-zero BlendWeight, i.e. it has a 100% chance."""
    return sum(1 for params in weathers.values() if params.get("BlendWeight")) <= 1


def build_variant(vanilla: Weathers, variant: dict) -> Weathers:
    """Apply multipliers and overrides to vanilla, returning the full resulting values."""
    multipliers = variant.get("multipliers") or {}
    step = variant.get("round_to")
    overrides = variant.get("overrides") or {}

    unknown = (set(variant.get("exclude") or []) | set(overrides)) - set(vanilla)
    if unknown:
        raise ValueError(f"Unknown regions (not in vanilla.yml): {sorted(unknown)}")

    exclude = set(variant.get("exclude") or []) | {sid for sid, w in vanilla.items() if is_single_weather(w)}
    excluded_overrides = exclude & set(overrides)
    if excluded_overrides:
        raise ValueError(f"Overrides for excluded or single-weather regions: {sorted(excluded_overrides)}")

    result = copy.deepcopy(vanilla)
    for sid, weathers in result.items():
        if sid in exclude:
            continue
        for weather_name, params in weathers.items():
            if weather_name in multipliers:
                original = params["BlendWeight"]
                params["BlendWeight"] = round_weight(original, original * multipliers[weather_name], step)

    for sid, weathers in overrides.items():
        for weather_name, params in weathers.items():
            result[sid].setdefault(weather_name, {}).update(params)

    return result


def diff_weathers(vanilla: Weathers, variant: Weathers) -> Weathers:
    """Return only the params whose values differ from vanilla."""
    changes: Weathers = {}
    for sid, weathers in variant.items():
        for weather_name, params in weathers.items():
            original = vanilla.get(sid, {}).get(weather_name, {})
            changed = {p: v for p, v in params.items() if original.get(p) != v}
            if changed:
                changes.setdefault(sid, {})[weather_name] = changed
    return changes


def generate_bpatch(changes: Weathers) -> str:
    """Generate bpatch .cfg content. Every nesting level needs {bpatch} to keep the other values."""
    lines = []
    for sid, weathers in changes.items():
        lines.append(f"{sid} : struct.begin {{bpatch}}")
        for weather_name, params in weathers.items():
            lines.append(f"   {weather_name} : struct.begin {{bpatch}}")
            for param_name, value in params.items():
                if param_name == "BlendWeight" or param_name.startswith("WeatherDuration"):
                    value = float(value)
                lines.append(f"      {param_name} = {format_value(value)}")
            lines.append("   struct.end")
        lines.append("struct.end")
    return "\n".join(lines) + "\n"


def write_cfg(content: str, output_path: Path) -> None:
    """Write a .cfg file like the game's own: UTF-8 with BOM and CRLF line endings."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"\xef\xbb\xbf" + content.replace("\n", "\r\n").encode("utf-8"))

#!/usr/bin/env python3
"""
Parser for STALKER 2 .cfg files.

The format is a tree of structs:

    KordonWeatherSelection : struct.begin {refkey=[1]}
       SID = KordonWeatherSelection
       Clearly : struct.begin
          BlendWeight = 30.f
       struct.end
    struct.end

Parameter order is not fixed, and numbers appear both as "30.f" and "30.0".
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STRUCT_BEGIN = re.compile(r"^\s*(\S+?)\s*:\s*struct\.begin\s*(?:\{(.*)\})?\s*$")
STRUCT_END = re.compile(r"^\s*struct\.end\s*$")
PARAM = re.compile(r"^\s*(\S+?)\s*=\s*(.*?)\s*$")


@dataclass
class Struct:
    """A struct node. `items` preserves the original order of params and child structs."""
    key: str
    options: str | None = None  # Raw header options, e.g. "refkey=[1]" or "bpatch"
    items: dict[str, Any] = field(default_factory=dict)

    @property
    def sid(self) -> str:
        return self.items.get("SID", self.key)

    @property
    def refkey(self) -> str | None:
        match = re.search(r"refkey=([^;}\s]+)", self.options or "")
        return match.group(1) if match else None

    def structs(self) -> dict[str, "Struct"]:
        return {k: v for k, v in self.items.items() if isinstance(v, Struct)}


def parse_value(value_str: str) -> Any:
    """Parse a config value: "true"/"false", "30.f"/"30.0"/"1.5f" as float, "1" as int, else string."""
    if value_str == "true":
        return True
    if value_str == "false":
        return False
    if re.fullmatch(r"-?\d+", value_str):
        return int(value_str)
    if re.fullmatch(r"-?(\d+\.\d*|\.\d+)f?|-?\d+f", value_str):
        return float(value_str.rstrip("f"))
    return value_str


def format_value(value: Any) -> str:
    """Format a Python value in the game's style, e.g. 45.0 -> "45.f", 12.5 -> "12.5f"."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value == int(value):
            return f"{int(value)}.f"
        return f"{value}f"
    return str(value)


def parse_cfg_text(text: str) -> list[Struct]:
    """Parse .cfg content into a list of top-level structs. Raises ValueError on unknown syntax."""
    roots: list[Struct] = []
    stack: list[Struct] = []

    for lineno, line in enumerate(text.lstrip("\ufeff").splitlines(), start=1):
        if not line.strip():
            continue

        if match := STRUCT_BEGIN.match(line):
            node = Struct(key=match.group(1), options=match.group(2))
            if stack:
                stack[-1].items[node.key] = node
            else:
                roots.append(node)
            stack.append(node)
        elif STRUCT_END.match(line):
            if not stack:
                raise ValueError(f"line {lineno}: unexpected struct.end")
            stack.pop()
        elif (match := PARAM.match(line)) and stack:
            stack[-1].items[match.group(1)] = parse_value(match.group(2))
        else:
            raise ValueError(f"line {lineno}: cannot parse {line!r}")

    if stack:
        raise ValueError(f"unterminated struct {stack[-1].key!r}")
    return roots


def parse_cfg_file(filepath: Path) -> list[Struct]:
    return parse_cfg_text(filepath.read_text(encoding="utf-8-sig"))


def merge(base: Struct, override: Struct) -> Struct:
    """Return a copy of `base` with `override`'s params and child structs merged on top."""
    merged = Struct(key=override.key, options=override.options, items=dict(base.items))
    for key, value in override.items.items():
        if isinstance(value, Struct) and isinstance(merged.items.get(key), Struct):
            merged.items[key] = merge(merged.items[key], value)
        else:
            merged.items[key] = value
    return merged


def resolve_inheritance(roots: list[Struct]) -> dict[str, Struct]:
    """
    Resolve refkey inheritance within a single file.

    Returns a SID -> fully resolved Struct mapping, in file order.
    """
    by_key = {node.key: node for node in roots}
    resolved: dict[str, Struct] = {}

    def resolve(node: Struct) -> Struct:
        if node.refkey is None:
            return node
        return merge(resolve(by_key[node.refkey]), node)

    for node in roots:
        resolved[node.sid] = resolve(node)
    return resolved


def load_weather_selections(filepath: Path) -> dict[str, Struct]:
    """Parse WeatherSelectionPrototypes.cfg into SID -> resolved Struct."""
    return resolve_inheritance(parse_cfg_file(filepath))

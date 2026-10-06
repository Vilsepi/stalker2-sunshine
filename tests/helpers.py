"""Shared helpers for the tests."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "src" / "config"
sys.path.insert(0, str(REPO_ROOT / "src"))

import yaml  # noqa: E402


def load_yaml(name: str) -> dict:
    return yaml.safe_load((CONFIG_DIR / name).read_text()) or {}

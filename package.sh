#!/bin/bash
# Generate the bpatch for a variant and pack it into a .pak with repak.
# Usage: ./package.sh [variant.yml]   (default: sunnier.yml)
set -e

cd "$(dirname "$0")"

VARIANT="${1:-sunnier.yml}"
MOD_DIR="dist/Sunshine_P"

python3 src/main.py "$VARIANT"

if ! command -v repak >/dev/null; then
    echo "Error: repak not found. Install it from https://github.com/trumank/repak/releases"
    echo "or with: cargo install --git https://github.com/trumank/repak repak_cli"
    exit 1
fi

rm -f "$MOD_DIR.pak"
repak pack "$MOD_DIR" "$MOD_DIR.pak"
echo "Packed $MOD_DIR.pak, copy it to <Game folder>\\Stalker2\\Content\\Paks\\~mods"

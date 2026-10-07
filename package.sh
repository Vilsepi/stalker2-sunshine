#!/bin/bash
# Generate the bpatch for each variant and pack it into dist/better-weather-<variant>.pak with repak.
# Usage: ./package.sh [variant.yml ...]   (paths, or names in src/config. Default: every variant except vanilla.yml)
set -e

if ! command -v repak >/dev/null; then
    echo "Error: repak not found. Install it from https://github.com/trumank/repak/releases"
    echo "or with: cargo install --git https://github.com/trumank/repak repak_cli"
    exit 1
fi

# Resolve paths relative to the current directory before changing directory
VARIANTS=()
for v in "$@"; do
    if [ -f "$v" ]; then v="$(realpath "$v")"; fi
    VARIANTS+=("$v")
done

cd "$(dirname "$0")"

if [ ${#VARIANTS[@]} -eq 0 ]; then
    for f in src/config/*.yml; do
        [ "$(basename "$f")" = "vanilla.yml" ] || VARIANTS+=("$(basename "$f")")
    done
fi

for v in "${VARIANTS[@]}"; do
    MOD_DIR="dist/better-weather-$(basename "$v" .yml)"
    python3 src/main.py "$v"
    rm -f "$MOD_DIR.pak"
    repak pack "$MOD_DIR" "$MOD_DIR.pak"
done

echo
echo "Copy one of the paks to <Game folder>\\Stalker2\\Content\\Paks\\~mods"

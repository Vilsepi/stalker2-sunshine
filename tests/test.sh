#!/bin/bash
# Run all tests. Use "./tests/test.sh unit" to only run the tests that don't need the original game config.
set -e

cd "$(dirname "$0")/.."

if [ "$1" = "unit" ]; then
    python3 -m unittest discover -s tests -p 'test_unit.py' -v
else
    python3 -m unittest discover -s tests -p 'test_*.py' -v
    python3 src/main.py sunnier.yml
fi

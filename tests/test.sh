#!/bin/bash
set -e

cd "$(dirname "$0")/.."

python3 -m unittest discover -s tests -v

python3 src/main.py sunnier.yml

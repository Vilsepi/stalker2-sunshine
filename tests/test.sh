#!/bin/bash

python3 src/main.py test.yml

echo "Printing the diff between the original and generated cfg files:"

diff original_config/WeatherSelectionPrototypes.cfg dist/output.cfg

sha256sum dist/output.cfg
sha256sum original_config/WeatherSelectionPrototypes.cfg

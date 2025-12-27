#!/bin/bash

# Combine chunks and verify that the combined file matches the original

# Sha256 checksum of the original WeatherSelectionPrototypes.cfg for game version 1.8.1
CHECKSUM_ORIGINAL="38b877fec418ad48214dd9be0f0d94999ff299f85029f38018d67db2533c6408"

cat original_chunked/*.cfg > combined.cfg

CHECKSUM_COMBINED=$(sha256sum combined.cfg | awk '{print $1}')
rm combined.cfg

if [ "$CHECKSUM_COMBINED" = "$CHECKSUM_ORIGINAL" ]; then
    echo "Checksum OK"
    exit 0
else
    echo "Error: Config file checksum mismatch!"
    echo "Expected: $CHECKSUM_ORIGINAL"
    echo "Got:      $CHECKSUM_COMBINED"
    exit 1
fi

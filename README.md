# stalker2-sunshine

This mod modifies the following file:

`Stalker2\Content\GameLite\GameData\WeatherSelectionPrototypes.cfg`

## Development

    cat src/config/original_chunked/*.cfg | sed 's/$/\r/' > src/config/combined.cfg

Convert all line endings to CRLF Windows line endings which the game uses:

    sed -i 's/$/\r/' src/config/original_chunked/*.cfg


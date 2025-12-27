# stalker2-sunshine

A tunable mod Stalker 2 to improve the always lousy weather.

This mod only modifies the following file:

`Stalker2\Content\GameLite\GameData\WeatherSelectionPrototypes.cfg`

## Development

    cat src/config/original_chunked/*.cfg | sed 's/$/\r/' > src/config/combined.cfg

Convert all line endings to CRLF Windows line endings which the game uses:

    sed -i 's/$/\r/' src/config/original_chunked/*.cfg

## Packaging

Use [repak](https://github.com/trumank/repak) to package the config file into a `.pak`, and copy it under `Game folder\Stalker2\Content\Paks\~mods`.

This will conflict with any other mod that modifies `WeatherSelectionPrototypes.cfg`.

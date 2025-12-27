# stalker2-sunshine

A tunable mod Stalker 2 to improve the always lousy weather.

This mod only modifies the following file:

`Stalker2\Content\GameLite\GameData\WeatherSelectionPrototypes.cfg`

## Usage

Create a patch file in YAML format in `src/config/` directory (e.g., `test.yml`).

Run the patcher:

    cd src
    python3 main.py test.yml

## Development

Convert all line endings to CRLF Windows line endings which the game uses:

    sed -i 's/$/\r/' src/config/original_chunked/*.cfg

## Packaging

Use [repak](https://github.com/trumank/repak) to package the config file into a `.pak`, and copy it under `Game folder\Stalker2\Content\Paks\~mods`.

This will conflict with any other mod that modifies `WeatherSelectionPrototypes.cfg`.

# stalker2-sunshine

A tunable mod for Stalker 2 to improve the always lousy weather.

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

## Weather mods by other authors

There is already a bunch of existing weather mods, but none of them did what I wanted.

- [Sunny Weather](https://www.nexusmods.com/stalker2heartofchornobyl/mods/296): This mod was my original inspiration. However, it forces nearly 100% clear weather everywhere, so it simplifies the game's weather too much.
- [Less Pleasant Weather 2](https://www.nexusmods.com/stalker2heartofchornobyl/mods/1555): This felt promising, but it uses an old version of the WeatherSelectionPrototypes.cfg as a base, so it is completely missing some weather config for the game.
- [Dynamic Weather Overhaul](https://www.nexusmods.com/stalker2heartofchornobyl/mods/164): Completely reworks the weather to be even more dramatic, and for example makes nights even darker.

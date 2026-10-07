# stalker2-sunshine

A tunable mod for Stalker 2 to improve the always lousy weather.

Built for game version 2.0.5/2.0.6 (base game only, the DLC's weather is not changed).

The mod is a `bpatch` file that only changes the weather weights it needs to, on top of the game's own:

`Stalker2/Content/GameLite/GameData/WeatherSelectionPrototypes.cfg`

Everything else in that file is kept as-is, so the mod keeps working when the game is updated, and only conflicts with other mods that change the same weather weights.

## Prerequisites

- Python 3
- Latest original [config files](https://www.nexusmods.com/stalker2heartofchornobyl/mods/1653)
- [repak](https://github.com/trumank/repak)

## Usage

A variant is a YAML file in `src/config/` (e.g. `sunnier.yml`). It multiplies each region's vanilla weights per weather type, with optional exact overrides per region. See `src/cfg_patcher.py` for the format.

Generate every variant (all of `src/config/*.yml` except `vanilla.yml`) and pack each into `dist/better-weather-<variant>.pak`, e.g. `dist/better-weather-sunnier.pak`:

    ./package.sh

Or only the given variants:

    ./package.sh sunnier.yml

This prints a table of each region's weather chances, vanilla vs. the variant. Copy one of the `.pak` files under `Game folder\Stalker2\Content\Paks\~mods`. Install only one variant at a time: they all contain the same patch file, so only one of them would take effect.

Packing needs [repak](https://github.com/trumank/repak). On Linux/WSL, install the prebuilt binary:

    curl -sSL https://github.com/trumank/repak/releases/download/v0.2.3/repak_cli-x86_64-unknown-linux-gnu.tar.xz \
      | tar xJ -C ~/.local/bin --strip-components=1 repak_cli-x86_64-unknown-linux-gnu/repak

To only generate the patch file without packing:

    python3 src/main.py sunnier.yml

The generated directory structure is:

    dist/better-weather-sunnier/Stalker2/Content/GameLite/GameData/WeatherSelectionPrototypes/WeatherSelectionPrototypes_patch_Sunshine.cfg

## Development

`src/config/vanilla.yml` is a readable snapshot of the game's weather config, and the base for all variants. To update it after a game patch, place the game's config under `original_config/` (not committed to git) and regenerate:

    original_config/v2.0.5/GameData/WeatherSelectionPrototypes.cfg

    python3 src/cfg_to_yml.py

The game config can be extracted with [FModel](https://fmodel.app/), or downloaded from config dumps on Nexus Mods.

Run all tests. The tests in `tests/test_game_config.py` need the original game config, and are skipped without it:

    ./tests/test.sh

Run only the unit tests that don't need the original game config (these also run on GitHub Actions):

    ./tests/test.sh unit

To view a weather config as a table:

    python3 src/yml_to_csv.py src/config/vanilla.yml

## Weather mods by other authors

There already exists several weather mods, but none of them did what I wanted.

- [Sunny Weather](https://www.nexusmods.com/stalker2heartofchornobyl/mods/296): This mod was my original inspiration. However, it forces nearly 100% clear weather everywhere, so it simplifies the game's weather too much.
- [Less Pleasant Weather 4](https://www.nexusmods.com/stalker2heartofchornobyl/mods/1555): Uses config file from an older game version, and does not use [bpatch](https://zonekit-support.stalker2.com/hc/en-us/articles/39357395461265-Config-patches) method.
- [Dynamic Weather Overhaul](https://www.nexusmods.com/stalker2heartofchornobyl/mods/164): Completely reworks the weather to be even more dramatic, and for example makes nights even darker.

#!/usr/bin/env python3
"""A helper script to view the yml weather data as a single glance table."""

import sys
import yaml

# All possible weather types and parameters
WEATHER_TYPES = ["Clearly", "Cloudy", "Stormy", "LightRainy", "Rainy"]
PARAMETERS = ["BlendWeight", "WeatherDurationMin", "WeatherDurationMax", "MaximumRepeatAmount", "MaximumCooldownWeatherAmount"]


def yaml_to_csv(yaml_file: str) -> None:
    """Read YAML file and print as tab-separated CSV."""
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    # Build header
    header = ["Region"]
    for weather in WEATHER_TYPES:
        for param in PARAMETERS:
            header.append(f"{weather}_{param}")

    print("\t".join(header))

    # Process each region
    for region, weather_data in data.items():
        row = [region]
        for weather in WEATHER_TYPES:
            for param in PARAMETERS:
                value = ""
                if weather_data and weather in weather_data:
                    if param in weather_data[weather]:
                        value = str(weather_data[weather][param])
                row.append(value)
        print("\t".join(row))


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <yaml_file>", file=sys.stderr)
        sys.exit(1)

    yaml_to_csv(sys.argv[1])


if __name__ == "__main__":
    main()

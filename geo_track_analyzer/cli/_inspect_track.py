import json
from pathlib import Path

import click

from geo_track_analyzer.model import Zones
from geo_track_analyzer.track import FITTrack
from geo_track_analyzer.visualize.dash.inspect import get_app


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option("--zones", type=click.Path(exists=True), default=None)
def main(filename: str, zones: str | None):
    click.echo("Extracting track from %s" % filename)
    file_path = Path(filename)

    hr_zones = None
    cadence_zones = None
    power_zones = None
    if zones is not None:
        with open(zones, "r") as f:
            _zones = json.load(f)

        hr_zones = _zones.get("heartrate", None)
        cadence_zones = _zones.get("cadence", None)
        power_zones = _zones.get("power", None)
        if hr_zones is not None:
            hr_zones = Zones.model_validate(hr_zones)
        if cadence_zones is not None:
            cadence_zones = Zones.model_validate(cadence_zones)
        if power_zones is not None:
            power_zones = Zones.model_validate(power_zones)

    if file_path.suffix == ".fit":
        track = FITTrack(
            filename,
            heartrate_zones=hr_zones,
            cadence_zones=cadence_zones,
            power_zones=power_zones,
        )
    else:
        click.echo(f"Invalid suffix: {file_path.suffix}")
        exit(1)

    app = get_app(track)
    app.run()


if __name__ == "__main__":
    main()

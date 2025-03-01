import json

from geo_track_analyzer.model import ZoneInterval, Zones

if __name__ == "__main__":
    cadence_zones = Zones(
        intervals=[
            ZoneInterval(start=None, end=60),
            ZoneInterval(start=60, end=75),
            ZoneInterval(start=75, end=85),
            ZoneInterval(start=85, end=None),
        ],
    )

    heartrate_zones = Zones(
        intervals=[
            ZoneInterval(start=None, end=138, name="Easy", color="#0796ce"),
            ZoneInterval(start=138, end=153, name="Fat Buring", color="#38d946"),
            ZoneInterval(start=153, end=160, name="Cardio", color="#fae800"),
            ZoneInterval(start=160, end=171, name="Hard", color="#e15904"),
            ZoneInterval(start=171, end=None, name="Peak", color="#dd070c"),
        ],
    )

    with open("zones.json", "w") as f:
        json.dump(
            {
                "cadence": cadence_zones.model_dump(),
                "heartrate": heartrate_zones.model_dump(),
            },
            f,
            indent=4,
        )

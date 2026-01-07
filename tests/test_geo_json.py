import importlib.resources
import json

from geo_track_analyzer.track import Track
from geo_track_analyzer.utils.geojson import (
    _convert_linestrings_collection,
    _convert_points_collection,
)
from tests import resources


def test_convert_points_collection() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "point_geo.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)
    print(data)

    track = _convert_points_collection(data, False)
    assert isinstance(track, Track)


def test_convert_linestrings_collection() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "line_geo.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)
    print(data)

    track = _convert_linestrings_collection(data, False)
    assert isinstance(track, Track)

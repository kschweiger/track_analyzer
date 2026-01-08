import importlib.resources
import json

import pytest

from geo_track_analyzer.exceptions import EmptyGeoJsonError, GeoJsonWithoutGeometryError
from geo_track_analyzer.track import Track
from geo_track_analyzer.utils.geojson import (
    _convert_linestrings_collection,
    _convert_linestrings_multisegment_collection,
    _convert_points_collection,
)
from tests import resources


def test_convert_points_collection() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "point_geo.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)

    track = _convert_points_collection(data, False, (0, 0))
    assert isinstance(track, Track)


def test_convert_points_collection_no_geo() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "point_no_coords_geo.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)

    track = _convert_points_collection(data, True, (0, 0))
    assert isinstance(track, Track)


def test_convert_points_collection_no_geo_fail() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "point_no_coords_geo.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)

    with pytest.raises(
        GeoJsonWithoutGeometryError, match="One or more features have no geometry"
    ):
        _convert_points_collection(data, False, (0, 0))


def test_convert_linestrings_collection() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "line_geo.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)

    track = _convert_linestrings_collection(data, False, (0, 0))
    assert isinstance(track, Track)


def test_convert_linestrings_collection_no_geo() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "line_no_coords_geo.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)

    track = _convert_linestrings_collection(data, True, (0, 0))
    assert isinstance(track, Track)


def test_convert_linestrings_collection_no_geo_fail() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "line_no_coords_geo.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)

    with pytest.raises(GeoJsonWithoutGeometryError, match="Geometry is missing"):
        _convert_linestrings_collection(data, False, (0, 0))


def test_convert_linestrings_multisegment_collection() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "line_geo_multi_segment.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)

    track = _convert_linestrings_multisegment_collection(data, False, (0, 0))
    assert isinstance(track, Track)
    assert track.n_segments == 2


def test_convert_linestrings_multisegment_collection_no_geo_fail() -> None:
    resource_files = importlib.resources.files(resources)
    with open(
        (resource_files / "line_no_coords_geo_multi_segment.json").joinpath(),  # type: ignore
        "rb",
    ) as f:
        data = json.load(f)

    with pytest.raises(GeoJsonWithoutGeometryError, match="Geometry is missing"):
        _convert_linestrings_multisegment_collection(data, False, (0, 0))


def test_convert_linestrings_multisegment_collection_no_geo() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "line_geo_multi_segment.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)

    track = _convert_linestrings_multisegment_collection(data, True, (0, 0))
    assert isinstance(track, Track)
    assert track.n_segments == 2


def test_convert_linestrings_multisegment_collection_no_segments() -> None:
    resource_files = importlib.resources.files(resources)
    with open((resource_files / "line_geo_multi_segment.json").joinpath(), "rb") as f:  # type: ignore
        data = json.load(f)
    data["features"] = []
    with pytest.raises(EmptyGeoJsonError):
        _convert_linestrings_multisegment_collection(data, False, (0, 0))

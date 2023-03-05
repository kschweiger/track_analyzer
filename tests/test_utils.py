from math import asin, degrees, isclose

import numpy as np
import pytest

from gpx_track_analyzer.enums import SegmentCharacter
from gpx_track_analyzer.model import Position2D, Position3D
from gpx_track_analyzer.utils import (
    calc_elevation_metrics,
    center_geolocation,
    distance,
    find_min_max,
)


def test_distance_far():
    p1 = Position2D(51.5073219, -0.1276474)  # London
    p2 = Position2D(48.8588897, 2.320041)  # Paris

    d = distance(p1, p2)

    assert int(d / 1000) == 342


def test_distance_close():
    p1 = Position2D(48.86104740612081, 2.3356136263202165)
    p2 = Position2D(48.861134753323505, 2.335389661859064)

    d = distance(p1, p2)

    assert int(d) == 19


def test_calc_elevation_metrics(mocker):
    mocker.patch("gpx_track_analyzer.utils.distance", return_value=150)

    positions = [
        Position3D(0, 0, 100),
        Position3D(0, 0, 200),
        Position3D(0, 0, 275),
        Position3D(0, 0, 175),
        Position3D(0, 0, 125),
    ]

    metrics = calc_elevation_metrics(positions)

    exp_uphill = 175
    exp_downhill = 150
    exp_slopes = [
        0,
        degrees(asin(100 / 150)),
        degrees(asin(75 / 150)),
        -degrees(asin(100 / 150)),
        -degrees(asin(50 / 150)),
    ]

    assert metrics.uphill == exp_uphill
    assert metrics.downhill == exp_downhill
    assert metrics.slopes == exp_slopes

    assert len(metrics.slopes) == len(positions)


def test_calc_elevation_metrics_nan(mocker):
    mocker.patch("gpx_track_analyzer.utils.distance", return_value=150)
    positions = [
        Position3D(0, 0, 100),
        Position3D(0, 0, 1000),
    ]

    metrics = calc_elevation_metrics(positions)

    assert metrics.slopes == [0.0, np.nan]


@pytest.mark.parametrize(
    ("coords", "exp_lat", "exp_lon"),
    [([(10, 0), (20, 0)], 15, 0), ([(0, 10), (0, 20)], 0, 15)],
)
def test_center_geolocation(coords, exp_lat, exp_lon):
    ret_lat, ret_lon = center_geolocation(coords)
    assert isclose(ret_lat, exp_lat)
    assert isclose(ret_lon, exp_lon)


@pytest.mark.parametrize(
    ("data", "exp_min_max"),
    [
        # ---------------------------------------------------
        (
            [
                ((0, 300), (10, 350), SegmentCharacter.ASCENT),
                ((10, 350), (20, 400), SegmentCharacter.ASCENT),
                ((20, 400), (30, 350), SegmentCharacter.DECENT),
                ((30, 350), (40, 320), SegmentCharacter.DECENT),
            ],
            [0, 20, 40],
        ),
        # ---------------------------------------------------
        # ([], []),
    ],
)
def test_find_min_max(data, exp_min_max):
    assert exp_min_max == find_min_max(data)

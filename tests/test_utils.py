from datetime import datetime, timedelta
from math import asin, degrees, isclose
from time import perf_counter
from typing import Literal, Type

import numpy as np
import pandas as pd
import pytest
from gpxpy.gpx import GPXTrack, GPXTrackPoint, GPXTrackSegment
from pytest_mock import MockerFixture

from geo_track_analyzer.model import (
    PointDistance,
    Position2D,
    Position3D,
    ZoneInterval,
    Zones,
)
from geo_track_analyzer.track import PyTrack
from geo_track_analyzer.utils.base import (
    calc_elevation_metrics,
    center_geolocation,
    distance,
    distance_to_location,
    fill_list,
    format_timedelta,
    get_distances,
    get_latitude_at_distance,
    get_longitude_at_distance,
    get_point_distance,
    get_points_inside_bounds,
    get_segment_base_area,
    interpolate_extension,
    interpolate_points,
    split_segment_by_id,
)
from geo_track_analyzer.utils.internal import (
    ExtensionFieldElement,
    get_extended_track_point,
    get_extension_value,
)
from geo_track_analyzer.utils.model import format_zones_for_digitize
from geo_track_analyzer.utils.track import generate_distance_segments


def test_distance_far() -> None:
    p1 = Position2D(latitude=51.5073219, longitude=-0.1276474)  # London
    p2 = Position2D(latitude=48.8588897, longitude=2.320041)  # Paris

    d = distance(p1, p2)

    assert int(d / 1000) == 342


def test_distance_close() -> None:
    p1 = Position2D(latitude=48.86104740612081, longitude=2.3356136263202165)
    p2 = Position2D(latitude=48.861134753323505, longitude=2.335389661859064)

    d = distance(p1, p2)

    assert int(d) == 19


def test_calc_elevation_metrics(mocker: MockerFixture) -> None:
    mocker.patch("geo_track_analyzer.utils.base.distance", return_value=150)

    positions = [
        Position3D(latitude=0, longitude=0, elevation=100),
        Position3D(latitude=0, longitude=0, elevation=200),
        Position3D(latitude=0, longitude=0, elevation=275),
        Position3D(latitude=0, longitude=0, elevation=175),
        Position3D(latitude=0, longitude=0, elevation=125),
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


def test_calc_elevation_metrics_nan(mocker: MockerFixture) -> None:
    mocker.patch("geo_track_analyzer.utils.base.distance", return_value=150)
    positions = [
        Position3D(latitude=0, longitude=0, elevation=100),
        Position3D(latitude=0, longitude=0, elevation=1000),
    ]

    metrics = calc_elevation_metrics(positions)

    assert metrics.slopes == [0.0, np.nan]


@pytest.mark.parametrize(
    ("coords", "exp_lat", "exp_lon"),
    [([(10, 0), (20, 0)], 15, 0), ([(0, 10), (0, 20)], 0, 15)],
)
def test_center_geolocation(
    coords: list[tuple[float, float]], exp_lat: float, exp_lon: float
) -> None:
    ret_lat, ret_lon = center_geolocation(coords)
    assert isclose(ret_lat, exp_lat)
    assert isclose(ret_lon, exp_lon)


def test_get_segment_base_area() -> None:
    points = [
        (48.86104740612081, 2.3356136263202165),
        (48.861134753323505, 2.335389661859064),
    ]
    area = get_segment_base_area(
        PyTrack(
            points,
            len(points) * [None],
            len(points) * [None],
        ).track.segments[0]
    )

    assert area > 0


def test_get_segment_base_area_long_line() -> None:
    points = [
        (48.86104740612081, 2.3356136263202165),
        (48.861134753323505, 2.3356136263202165),
    ]
    assert (
        get_segment_base_area(
            PyTrack(
                points,
                len(points) * [None],
                len(points) * [None],
            ).track.segments[0]
        )
        == 0
    )


def test_get_segment_base_area_lat_line() -> None:
    points = [
        (48.86104740612081, 2.3356136263202165),
        (48.86104740612081, 2.335389661859064),
    ]
    assert (
        get_segment_base_area(
            PyTrack(
                points,
                len(points) * [None],
                len(points) * [None],
            ).track.segments[0]
        )
        == 0
    )


@pytest.mark.parametrize(
    ("value", "distance", "to_east", "exp_value"),
    [(47.996, 111.2, True, 47.997), (47.996, 111.2, False, 47.995)],
)
def test_get_latitude_at_distance(
    value: float, distance: float, to_east: bool, exp_value: float
) -> None:
    assert (
        round(
            get_latitude_at_distance(
                Position2D(latitude=value, longitude=1), distance, to_east
            ),
            3,
        )
        == exp_value
    )


@pytest.mark.parametrize(
    ("value", "distance", "to_north", "exp_value"),
    [(7.854, 74.41, True, 7.855), (7.854, 74.41, False, 7.853)],
)
def test_get_longitude_at_distance(
    value: float, distance: float, to_north: bool, exp_value: float
) -> None:
    assert (
        round(
            get_longitude_at_distance(
                Position2D(latitude=47.996, longitude=value), distance, to_north
            ),
            3,
        )
        == exp_value
    )


@pytest.mark.parametrize(
    ("v1_point", "v2_points", "exp_shape"),
    [
        ([[0, 1], [1, 1], [2, 2]], [[1, 1], [2, 2]], (3, 2)),
        ([[0, 1], [1, 1], [2, 2]], [[1, 1]], (3, 1)),
    ],
)
def test_get_distance(
    v1_point: list[list[int]], v2_points: list[list[int]], exp_shape: tuple[int, int]
) -> None:
    distances = get_distances(np.array(v1_point), np.array(v2_points))

    assert isinstance(distances, np.ndarray)
    assert distances.shape == exp_shape


def test_get_distance_computation() -> None:
    v1_points = [[0, 1], [1, 1], [2, 2]]
    v2_points = [[1, 1], [2, 2]]

    distances_full = get_distances(np.array(v1_points), np.array(v2_points))
    distances_v2_first = get_distances(np.array(v1_points), np.array([v2_points[0]]))
    distances_v2_second = get_distances(np.array(v1_points), np.array([v2_points[1]]))

    assert (distances_full[:, 0] == distances_v2_first[:, 0]).all()
    assert (distances_full[:, 1] == distances_v2_second[:, 0]).all()

    indiv_values = np.array(
        [
            [
                distance(
                    Position2D(latitude=v1_points[0][0], longitude=v1_points[0][1]),
                    Position2D(latitude=v2_points[0][0], longitude=v2_points[0][1]),
                ),
                distance(
                    Position2D(latitude=v1_points[0][0], longitude=v1_points[0][1]),
                    Position2D(latitude=v2_points[1][0], longitude=v2_points[1][1]),
                ),
            ],
            [
                distance(
                    Position2D(latitude=v1_points[1][0], longitude=v1_points[1][1]),
                    Position2D(latitude=v2_points[0][0], longitude=v2_points[0][1]),
                ),
                distance(
                    Position2D(latitude=v1_points[1][0], longitude=v1_points[1][1]),
                    Position2D(latitude=v2_points[1][0], longitude=v2_points[1][1]),
                ),
            ],
            [
                distance(
                    Position2D(latitude=v1_points[2][0], longitude=v1_points[2][1]),
                    Position2D(latitude=v2_points[0][0], longitude=v2_points[0][1]),
                ),
                distance(
                    Position2D(latitude=v1_points[2][0], longitude=v1_points[2][1]),
                    Position2D(latitude=v2_points[1][0], longitude=v2_points[1][1]),
                ),
            ],
        ]
    )

    assert np.isclose(indiv_values, distances_full).all()


@pytest.mark.parametrize(
    ("points", "bounds", "exp_array"),
    [
        (
            [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
            (2.9, 2.9, 4.1, 4.1),
            [(0, False), (1, False), (2, True), (3, True), (4, False)],
        ),
        (
            [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (4, 4), (3, 3), (1, 1)],
            (2.9, 2.9, 4.1, 4.1),
            [
                (0, False),
                (1, False),
                (2, True),
                (3, True),
                (4, False),
                (5, True),
                (6, True),
                (7, False),
            ],
        ),
    ],
)
def test_get_points_inside_bounds(
    points: list[tuple[int, int]],
    bounds: tuple[float, float, float, float],
    exp_array: list[tuple[int, bool]],
) -> None:
    test_segment = GPXTrackSegment()
    for lat, lng in points:
        test_segment.points.append(GPXTrackPoint(lat, lng))

    assert get_points_inside_bounds(test_segment, *bounds) == exp_array


def test_split_segment_by_id() -> None:
    in_segment = GPXTrackSegment()
    in_segment.points = [
        GPXTrackPoint(1, 1),
        GPXTrackPoint(2, 2),
        GPXTrackPoint(3, 3),
        GPXTrackPoint(4, 4),
        GPXTrackPoint(5, 5),
        GPXTrackPoint(6, 6),
        GPXTrackPoint(7, 7),
        GPXTrackPoint(8, 8),
        GPXTrackPoint(9, 9),
        GPXTrackPoint(10, 10),
    ]

    ret_segments = split_segment_by_id(in_segment, [(1, 4), (6, 8)])

    assert len(ret_segments) == 2
    for ret_point, exp_point in zip(
        ret_segments[0].points,
        [
            GPXTrackPoint(2, 2),
            GPXTrackPoint(3, 3),
            GPXTrackPoint(4, 4),
            GPXTrackPoint(5, 5),
        ],
    ):
        assert ret_point.latitude == exp_point.latitude
        assert ret_point.longitude == exp_point.longitude

    for ret_point, exp_point in zip(
        ret_segments[1].points,
        [
            GPXTrackPoint(7, 7),
            GPXTrackPoint(8, 8),
            GPXTrackPoint(9, 9),
        ],
    ):
        assert ret_point.latitude == exp_point.latitude
        assert ret_point.longitude == exp_point.longitude


def test_get_extension_value() -> None:
    point = GPXTrackPoint(latitude=1, longitude=1)
    elem = ExtensionFieldElement("some_key", "some_value")
    point.extensions.append(elem)

    assert get_extension_value(point, "some_key") == "some_value"


@pytest.mark.parametrize(
    (
        "segment_idx",
        "test_lat",
        "test_long",
        "exp_point",
        "exp_point_idx_abs",
        "exp_segment_idx",
        "exp_segment_point_idx",
    ),
    [
        (None, 3.01, 3.01, GPXTrackPoint(3, 3), 2, 0, 2),
        (None, 7.01, 7.01, GPXTrackPoint(7, 7), 6, 1, 2),
        (0, 3.01, 3.01, GPXTrackPoint(3, 3), 2, 0, 2),
        (0, 7.01, 7.01, GPXTrackPoint(4, 4), 3, 0, 3),
        (1, 7.01, 7.01, GPXTrackPoint(7, 7), 2, 1, 2),
    ],
)
def test_get_point_distance_in_segment(
    segment_idx: int,
    test_lat: float,
    test_long: float,
    exp_point: GPXTrackPoint,
    exp_point_idx_abs: int,
    exp_segment_idx: int,
    exp_segment_point_idx: int,
) -> None:
    segment_1 = GPXTrackSegment()
    segment_1.points = [
        GPXTrackPoint(1, 1),
        GPXTrackPoint(2, 2),
        GPXTrackPoint(3, 3),
        GPXTrackPoint(4, 4),
    ]

    segment_2 = GPXTrackSegment()
    segment_2.points = [
        GPXTrackPoint(5, 5),
        GPXTrackPoint(6, 6),
        GPXTrackPoint(7, 7),
        GPXTrackPoint(8, 8),
    ]

    track = GPXTrack()
    track.segments = [segment_1, segment_2]

    res = get_point_distance(track, segment_idx, test_lat, test_long)

    assert isinstance(res, PointDistance)

    assert res.point.latitude == exp_point.latitude
    assert res.point.longitude == exp_point.longitude
    assert res.distance > 0
    assert res.point_idx_abs == exp_point_idx_abs
    assert res.segment_idx == exp_segment_idx
    assert res.segment_point_idx == exp_segment_point_idx


@pytest.mark.parametrize(
    ("td", "exp"),
    [
        (timedelta(seconds=86400), "24:00:00"),
        (timedelta(seconds=3600), "01:00:00"),
        (timedelta(seconds=60), "00:01:00"),
        (timedelta(seconds=1), "00:00:01"),
        (timedelta(seconds=3610), "01:00:10"),
        (timedelta(seconds=121), "00:02:01"),
        (timedelta(seconds=61), "00:01:01"),
        (timedelta(seconds=86400 * 2), "48:00:00"),
    ],
)
def test_format_timedelta(td: timedelta, exp: str) -> None:
    assert format_timedelta(td) == exp


@pytest.mark.parametrize(
    ("elevation_1", "elevation_2", "exp_elevations"),
    [(None, None, None), (100, 600, [100, 200, 300, 400, 500, 600])],
)
@pytest.mark.parametrize(
    ("seconds_1", "seconds_2", "exp_seconds"),
    [(None, None, None), (0, 50, [0, 10, 20, 30, 40, 50])],
)
def test_interpolate_points(
    elevation_1: None | int,
    elevation_2: None | int,
    exp_elevations: None | list[int],
    seconds_1: None | int,
    seconds_2: None | int,
    exp_seconds: None | list[int],
) -> None:
    time_1: None | datetime
    if seconds_1 is not None:
        time_1 = datetime(2023, 1, 1, 12, 0, seconds_1)
    else:
        time_1 = None

    time_2: None | datetime
    if seconds_2 is not None:
        time_2 = datetime(2023, 1, 1, 12, 0, seconds_2)
    else:
        time_2 = None

    point_1 = get_extended_track_point(1.100, 1.100, elevation_1, time_1, {})
    point_2 = get_extended_track_point(1.105, 1.105, elevation_2, time_2, {})
    ret_points = interpolate_points(point_1, point_2, 150)

    assert ret_points is not None
    assert len(ret_points) == 6

    exp_vals = [1.100, 1.101, 1.102, 1.103, 1.104, 1.105]
    assert [p.latitude for p in ret_points] == exp_vals
    assert [p.longitude for p in ret_points] == exp_vals

    if exp_elevations is not None:
        assert [p.elevation for p in ret_points] == exp_elevations

    if exp_seconds is not None:
        exp_times = [datetime(2023, 1, 1, 12, 0, s) for s in exp_seconds]
        assert [p.time for p in ret_points] == exp_times


def test_interpolate_points_with_extensions() -> None:
    point_1 = get_extended_track_point(
        1.100, 1.100, None, None, {"heartrate": 100, "cadence": 80, "power": 300}
    )
    point_2 = get_extended_track_point(
        1.105, 1.105, None, None, {"heartrate": 150, "cadence": 90, "power": 350}
    )

    exp_hr = [100, 100, 100, 100, 100, 150]
    exp_cd = [80, 80, 80, 80, 80, 90]
    exp_pw = [300, 300, 300, 300, 300, 350]

    ret_points = interpolate_points(point_1, point_2, 150)

    assert ret_points is not None

    assert [int(get_extension_value(p, "heartrate")) for p in ret_points] == exp_hr
    assert [int(get_extension_value(p, "cadence")) for p in ret_points] == exp_cd
    assert [int(get_extension_value(p, "power")) for p in ret_points] == exp_pw


@pytest.mark.parametrize(
    ("interpolation_type", "exp_values"),
    [
        ("copy-forward", [100, 100, 100, 100, 100, 150]),
        ("meet-center", [100, 100, 100, 150, 150, 150]),
        ("linear", [100, 110, 120, 130, 140, 150]),
    ],
)
@pytest.mark.parametrize("convert_type", [int, float])
def test_interpolate_extension(
    interpolation_type: Literal["copy-forward", "meet-center", "linear"],
    exp_values: list[int],
    convert_type: Type[int] | Type[float],
) -> None:
    point_1 = get_extended_track_point(1.100, 1.100, None, None, {"value": 100})
    point_2 = get_extended_track_point(1.105, 1.105, None, None, {"value": 150})

    values = interpolate_extension(
        point_1, point_2, "value", 6, interpolation_type, convert_type
    )

    assert values is not None
    assert len(values) == 6

    assert all(isinstance(v, convert_type) for v in values)
    _exp_values = [convert_type(v) for v in exp_values]
    assert values == _exp_values


@pytest.mark.parametrize(
    ("ext_1", "ext_2"), [({}, {}), ({"value": 150}, {}), ({}, {"value": 150})]
)
def test_interpolate_extension_not_possible(ext_1: dict, ext_2: dict) -> None:
    point_1 = get_extended_track_point(1.100, 1.100, None, None, {})
    point_2 = get_extended_track_point(1.105, 1.105, None, None, {"value": 150})
    assert interpolate_extension(point_1, point_2, "value", 6, "linear", int) == [
        None for _ in range(6)
    ]


@pytest.mark.flaky(retries=3)
@pytest.mark.parametrize("n_points", [500, 1000, 1500, 10_000])
def test_closest_point_timing(n_points: int) -> None:
    from gpxpy.geo import Location

    def run(track: PyTrack, point: tuple[float, float]) -> None:
        track.track.get_nearest_location(Location(*point))

    def run_vec(track: PyTrack, point: tuple[float, float]) -> None:
        arr = np.array(
            [(p.latitude, p.longitude) for p in track.track.segments[0].points]
        )
        distances = distance_to_location(arr, point)
        np.argmin(distances)

    curr_coords = (1.0, 1.0)
    offset = 0.0001
    pts = [curr_coords]
    for _ in range(n_points - 1):
        lat, lng = curr_coords
        curr_coords = (lat + offset, lng + offset)
        pts.append(curr_coords)
    track = PyTrack(points=pts, elevations=None, times=None)

    points = track.track.segments[0].points
    loc = points[len(points) // 2]

    pre = perf_counter()
    run(track, (loc.latitude, loc.longitude))
    time_gpxpy = perf_counter() - pre

    pre = perf_counter()
    run_vec(track, (loc.latitude, loc.longitude))
    time_distance_to_location = perf_counter() - pre

    pre = perf_counter()
    track.get_closest_point(0, loc.latitude, loc.longitude)
    time_closest_point = perf_counter() - pre

    assert time_gpxpy > time_distance_to_location
    assert time_gpxpy > time_closest_point


@pytest.mark.parametrize(
    ("values", "exp_values"),
    [
        ([None, None, 1, 2], [1, 1, 1, 2]),
        ([1, 2, None, None], [1, 2, 2, 2]),
        ([None, None, 1, 2, None, None], [1, 1, 1, 2, 2, 2]),
        ([1, None, None, 4], [1, 2, 3, 4]),
        ([1, None, None, 4, None, None, 7], [1, 2, 3, 4, 5, 6, 7]),
    ],
)
def test_fill_list(values: list[None | float], exp_values: list[float]) -> None:
    assert fill_list(values) == exp_values


@pytest.mark.parametrize(
    ("names", "colors", "exp_names", "exp_colors"),
    [
        ([None, None, None], [None, None, None], ["Zone 1", "Zone 2", "Zone 3"], None),
        (
            ["Some Zone 1", "Some Zone 2", "Some Zone 3"],
            [None, None, None],
            ["Some Zone 1", "Some Zone 2", "Some Zone 3"],
            None,
        ),
        (
            [None, None, None],
            ["#FFFFFF", "#222222", "#000000"],
            ["Zone 1", "Zone 2", "Zone 3"],
            ["#FFFFFF", "#222222", "#000000"],
        ),
    ],
)
def test_format_zones_for_digitize(
    names: list[None] | list[str],
    colors: list[None] | list[str],
    exp_names: list[str],
    exp_colors: None | list[str],
) -> None:
    zones = Zones(
        intervals=[
            ZoneInterval(start=None, end=100, name=names[0], color=colors[0]),
            ZoneInterval(start=100, end=150, name=names[1], color=colors[1]),
            ZoneInterval(start=150, end=None, name=names[2], color=colors[2]),
        ],
    )

    vals, ret_names, ret_colors = format_zones_for_digitize(zones)

    for ret_name, exp_name in zip(ret_names, exp_names):
        assert ret_name.startswith(exp_name)

    assert ret_colors == exp_colors
    assert (vals == np.array([-np.inf, 100, 150, np.inf])).all()


@pytest.mark.parametrize(
    ("data", "distance", "exp_segments"),
    [
        (
            pd.DataFrame(
                {
                    "cum_distance_moving": [0, 100, 200, 300, 400, 500, 600, 700],
                    "segment": [0, 0, 0, 0, 0, 1, 1, 1],
                }
            ),
            2000,
            pd.Series([0, 0, 0, 0, 0, 0, 0, 0]),
        ),
        (
            pd.DataFrame(
                {
                    "cum_distance_moving": [0, 100, 200, 300, 400, 500, 600, 700],
                    "segment": [0, 0, 0, 0, 0, 0, 0, 0],
                }
            ),
            200,
            pd.Series([0, 0, 1, 1, 2, 2, 3, 3]),
        ),
        (
            pd.DataFrame(
                {
                    "cum_distance_moving": [0, 100, 200, 300, 400, 500, 600],
                    "segment": [0, 0, 0, 0, 0, 0, 0],
                }
            ),
            200,
            pd.Series([0, 0, 1, 1, 2, 2, 3]),
        ),
    ],
)
def test_generate_distance_segments(
    data: pd.DataFrame, distance: int, exp_segments: pd.Series
) -> None:
    split_data = generate_distance_segments(data, distance)

    assert split_data["segment"].compare(exp_segments).empty

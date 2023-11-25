from datetime import timedelta
from math import asin, degrees, isclose

import numpy as np
import pytest
from gpxpy.gpx import GPXTrack, GPXTrackPoint, GPXTrackSegment

from geo_track_analyzer.model import PointDistance, Position2D, Position3D
from geo_track_analyzer.track import PyTrack
from geo_track_analyzer.utils.base import (
    ExtensionFieldElement,
    calc_elevation_metrics,
    center_geolocation,
    distance,
    format_timedelta,
    get_distances,
    get_extension_value,
    get_latitude_at_distance,
    get_longitude_at_distance,
    get_point_distance,
    get_points_inside_bounds,
    get_segment_base_area,
    split_segment_by_id,
)


def test_distance_far() -> None:
    p1 = Position2D(51.5073219, -0.1276474)  # London
    p2 = Position2D(48.8588897, 2.320041)  # Paris

    d = distance(p1, p2)

    assert int(d / 1000) == 342


def test_distance_close() -> None:
    p1 = Position2D(48.86104740612081, 2.3356136263202165)
    p2 = Position2D(48.861134753323505, 2.335389661859064)

    d = distance(p1, p2)

    assert int(d) == 19


def test_calc_elevation_metrics(mocker) -> None:
    mocker.patch("geo_track_analyzer.utils.base.distance", return_value=150)

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


def test_calc_elevation_metrics_nan(mocker) -> None:
    mocker.patch("geo_track_analyzer.utils.base.distance", return_value=150)
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
def test_center_geolocation(coords, exp_lat, exp_lon) -> None:
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
def test_get_latitude_at_distance(value, distance, to_east, exp_value) -> None:
    assert (
        round(get_latitude_at_distance(Position2D(value, 1), distance, to_east), 3)
        == exp_value
    )


@pytest.mark.parametrize(
    ("value", "distance", "to_north", "exp_value"),
    [(7.854, 74.41, True, 7.855), (7.854, 74.41, False, 7.853)],
)
def test_get_longitude_at_distance(value, distance, to_north, exp_value) -> None:
    assert (
        round(
            get_longitude_at_distance(Position2D(47.996, value), distance, to_north), 3
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
def test_get_distance(v1_point, v2_points, exp_shape) -> None:
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
                distance(Position2D(*v1_points[0]), Position2D(*v2_points[0])),
                distance(Position2D(*v1_points[0]), Position2D(*v2_points[1])),
            ],
            [
                distance(Position2D(*v1_points[1]), Position2D(*v2_points[0])),
                distance(Position2D(*v1_points[1]), Position2D(*v2_points[1])),
            ],
            [
                distance(Position2D(*v1_points[2]), Position2D(*v2_points[0])),
                distance(Position2D(*v1_points[2]), Position2D(*v2_points[1])),
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
def test_get_points_inside_bounds(points, bounds, exp_array) -> None:
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

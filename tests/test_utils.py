from math import asin, degrees, isclose

import numpy as np
import pytest
from gpxpy.gpx import GPXTrackPoint, GPXTrackSegment

from gpx_track_analyzer.model import Position2D, Position3D
from gpx_track_analyzer.track import PyTrack
from gpx_track_analyzer.utils import (
    calc_elevation_metrics,
    center_geolocation,
    distance,
    get_color_gradient,
    get_distances,
    get_latitude_at_distance,
    get_longitude_at_distance,
    get_points_inside_bounds,
    get_segment_base_area,
    hex_to_rgb,
    split_segment_by_id,
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
    ("in_str", "exp_out"),
    [
        ("#FFFFFF", (255, 255, 255)),  # White
        ("#000000", (0, 0, 0)),  # Black
        ("#00FF00", (0, 255, 0)),  # Green
        ("#FF0000", (255, 0, 0)),  # Red
        ("#0000FF", (0, 0, 255)),  # Blue
    ],
)
def test_hex_to_rgb(in_str, exp_out):
    assert hex_to_rgb(in_str) == exp_out


def test_get_color_gradient():
    gradient = get_color_gradient("#FFFFFF", "#000000", 5)
    assert len(gradient) == 5
    assert gradient[0] == "#FFFFFF"
    assert gradient[-1] == "#000000"


def test_get_segment_base_area():
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


def test_get_segment_base_area_long_line():
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


def test_get_segment_base_area_lat_line():
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
def test_get_latitude_at_distance(value, distance, to_east, exp_value):
    assert (
        round(get_latitude_at_distance(Position2D(value, 1), distance, to_east), 3)
        == exp_value
    )


@pytest.mark.parametrize(
    ("value", "distance", "to_north", "exp_value"),
    [(7.854, 74.41, True, 7.855), (7.854, 74.41, False, 7.853)],
)
def test_get_longitude_at_distance(value, distance, to_north, exp_value):
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
def test_get_distance(v1_point, v2_points, exp_shape):
    distances = get_distances(np.array(v1_point), np.array(v2_points))

    assert isinstance(distances, np.ndarray)
    assert distances.shape == exp_shape


def test_get_distance_computation():
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

    assert (indiv_values == distances_full).all()


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
def test_get_points_inside_bounds(points, bounds, exp_array):
    test_segment = GPXTrackSegment()
    for lat, lng in points:
        test_segment.points.append(GPXTrackPoint(lat, lng))

    assert get_points_inside_bounds(test_segment, *bounds) == exp_array


def test_split_segment_by_id():
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

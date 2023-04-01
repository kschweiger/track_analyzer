from unittest.mock import MagicMock

import numpy as np
import pytest
from gpxpy.gpx import GPXBounds

from gpx_track_analyzer.compare import (
    check_segment_bound_overlap,
    convert_segment_to_plate,
    derive_plate_bins,
    get_distances,
    get_segment_overlap,
)
from gpx_track_analyzer.model import Position2D
from gpx_track_analyzer.track import PyTrack
from gpx_track_analyzer.utils import distance


@pytest.mark.parametrize(
    ("compare_points", "result"),
    [
        # Same as reference
        ([(1, 1), (1.5, 1.5), (2, 2)], True),
        # Paralell to reference and fully contained in ref bounds
        ([(1.1, 1.1), (1.2, 1.2), (1.3, 1.3)], True),
        # Reference fully contained inside
        ([(0.5, 0.5), (2, 2), (3, 3)], True),
        ([(1, 3), (2, 1.5), (0.5, 2)], True),
        ([(2, 1), (2.2, 1), (2.4, 1), (2.6, 1)], False),
    ],
)
def test_check_segment_bound_overlap(compare_points, result):
    reference_points = [(1, 1), (1.5, 1.5), (2, 2)]

    reference_segment = PyTrack(
        reference_points, len(reference_points) * [None], len(reference_points) * [None]
    ).track.segments[0]

    check_track = PyTrack(
        compare_points, len(compare_points) * [None], len(compare_points) * [None]
    ).track.segments[0]

    assert check_segment_bound_overlap(reference_segment, [check_track]) == [result]


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


def test_derive_plate_bins():
    width = 100
    bounds_min_latitude = 47.99
    bounds_min_longitude = 7.85
    bounds_max_latitude = 48
    bounds_max_longitude = 7.87
    bins_lat, bins_long = derive_plate_bins(
        width,
        bounds_min_latitude,
        bounds_min_longitude,
        bounds_max_latitude,
        bounds_max_longitude,
    )

    assert bins_lat[-1][0] > bounds_max_latitude
    assert bins_lat[0][0] < bounds_min_latitude

    assert bins_long[-1][1] > bounds_max_longitude
    assert bins_long[0][1] < bounds_min_longitude

    assert (
        width * 0.999
        <= distance(
            Position2D(bins_lat[0][0], bins_lat[0][1]),
            Position2D(bins_lat[1][0], bins_lat[1][1]),
        )
        < width * 1.001
    )

    assert (
        width
        <= distance(
            Position2D(bins_long[0][0], bins_long[0][1]),
            Position2D(bins_long[1][0], bins_long[1][1]),
        )
        < 2 * width
    )


@pytest.mark.parametrize(
    ("points", "patch_bins", "normalize", "exp_plate"),
    [
        (
            [(1, 1), (2, 2), (3, 3)],
            ([(0, 0), (1, 0), (2, 0), (3, 0)], [(0, 0), (0, 1), (0, 2), (0, 3)]),
            False,
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
        ),
        (
            [(1, 1), (1.5, 1.5), (2, 2), (3, 3)],
            ([(0, 0), (1, 0), (2, 0), (3, 0)], [(0, 0), (0, 1), (0, 2), (0, 3)]),
            False,
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 2, 0, 0], [0, 0, 0, 0]]),
        ),
        (
            [(1, 1), (1.5, 1.5), (2, 2), (3, 3)],
            ([(0, 0), (1, 0), (2, 0), (3, 0)], [(0, 0), (0, 1), (0, 2), (0, 3)]),
            True,
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
        ),
    ],
)
def test_convert_segment_to_plate(mocker, points, patch_bins, normalize, exp_plate):
    mocker.patch(
        "gpx_track_analyzer.compare.derive_plate_bins", return_value=patch_bins
    )

    grid_width = 100
    track = PyTrack(points, len(points) * [None], len(points) * [None])
    bounds = track.track.segments[0].get_bounds()
    plate = convert_segment_to_plate(
        track.track.segments[0],
        grid_width,
        bounds.min_latitude,
        bounds.min_longitude,
        bounds.max_latitude,
        bounds.max_longitude,
        normalize=normalize,
    )

    assert isinstance(plate, np.ndarray)
    assert (plate == exp_plate).all()


@pytest.mark.parametrize(
    ("plate_base", "plate_match", "exp_overlap"),
    [
        (
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
            1,
        ),
        (
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
            np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
            0.75,
        ),
        (
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
            np.array([[1, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]),
            0,
        ),
    ],
)
def test_get_segment_overlap(mocker, plate_base, plate_match, exp_overlap):
    mocker.patch(
        "gpx_track_analyzer.compare.convert_segment_to_plate",
        side_effect=[plate_base, plate_match],
    )

    base_segment = MagicMock()
    base_segment.get_bounds = lambda: GPXBounds(1, 1, 1, 1)
    match_segment = MagicMock()
    match_segment.get_bounds = lambda: GPXBounds(1, 1, 1, 1)

    assert get_segment_overlap(base_segment, match_segment, 100)

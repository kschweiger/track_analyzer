import numpy as np
import pytest

from gpx_track_analyzer.compare import (
    check_segment_bound_overlap,
    derive_plate_bins,
    get_distances,
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

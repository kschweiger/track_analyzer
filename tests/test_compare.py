from unittest.mock import MagicMock

import numpy as np
import pytest
from gpxpy.gpx import GPXBounds, GPXTrackPoint, GPXTrackSegment
from pytest_mock import MockerFixture

from geo_track_analyzer.compare import (
    _extract_ranges,
    check_segment_bound_overlap,
    convert_segment_to_plate,
    derive_plate_bins,
    get_segment_overlap,
)
from geo_track_analyzer.model import PointDistance, Position2D, SegmentOverlap
from geo_track_analyzer.track import PyTrack
from geo_track_analyzer.utils.base import distance


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
def test_check_segment_bound_overlap(
    compare_points: list[tuple[float, float]], result: bool
) -> None:
    reference_points = [(1, 1), (1.5, 1.5), (2, 2)]

    reference_segment = PyTrack(
        reference_points, len(reference_points) * [None], len(reference_points) * [None]
    ).track.segments[0]

    check_track = PyTrack(
        compare_points, len(compare_points) * [None], len(compare_points) * [None]
    ).track.segments[0]

    assert check_segment_bound_overlap(reference_segment, [check_track]) == [result]


def test_derive_plate_bins() -> None:
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
            Position2D(latitude=bins_lat[0][0], longitude=bins_lat[0][1]),
            Position2D(latitude=bins_lat[1][0], longitude=bins_lat[1][1]),
        )
        < width * 1.001
    )

    assert (
        width
        <= distance(
            Position2D(latitude=bins_long[0][0], longitude=bins_long[0][1]),
            Position2D(latitude=bins_long[1][0], longitude=bins_long[1][1]),
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
def test_convert_segment_to_plate(
    mocker: MockerFixture,
    points: list[tuple[float, float]],
    patch_bins: tuple[list[tuple[float, float]], list[tuple[float, float]]],
    normalize: bool,
    exp_plate: np.ndarray,
) -> None:
    mocker.patch(
        "geo_track_analyzer.compare.derive_plate_bins", return_value=patch_bins
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
            [1],
        ),
        (
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
            np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
            [2 / 3],
        ),
        (
            np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]),
            np.array([[1, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]),
            [0],
        ),
    ],
)
def test_get_segment_overlap(
    mocker: MockerFixture,
    plate_base: np.ndarray,
    plate_match: np.ndarray,
    exp_overlap: list[float],
) -> None:
    mocker.patch(
        "geo_track_analyzer.compare.convert_segment_to_plate",
        side_effect=[plate_base, plate_match],
    )

    mocker.patch(
        "geo_track_analyzer.compare.get_point_distance",
        side_effect=[
            PointDistance(
                point=GPXTrackPoint(1, 1),
                distance=10,
                point_idx_abs=0,
                segment_idx=0,
                segment_point_idx=0,
            ),
            PointDistance(
                point=GPXTrackPoint(2, 2),
                distance=10,
                point_idx_abs=3,
                segment_idx=0,
                segment_point_idx=3,
            ),
        ],
    )

    base_segment = MagicMock()
    base_segment.get_bounds = lambda: GPXBounds(1, 1, 1, 1)
    match_segment = MagicMock()
    match_segment.get_bounds = lambda: GPXBounds(1, 1, 1, 1)
    match_segment.points = [GPXTrackPoint(1, 1), GPXTrackPoint(2, 2)]

    overlap_datas = get_segment_overlap(
        base_segment, match_segment, 100, overlap_threshold=0.0
    )

    assert isinstance(overlap_datas[0], SegmentOverlap)
    assert len(overlap_datas) == len(exp_overlap)

    for data, overlap in zip(overlap_datas, exp_overlap):
        assert data.overlap == overlap


def test_get_segment_overlap_multi() -> None:
    base_segment = GPXTrackSegment()
    base_segment.points = [
        GPXTrackPoint(1, 1),
        GPXTrackPoint(1, 2),
        GPXTrackPoint(1, 3),
        GPXTrackPoint(1, 4),
        GPXTrackPoint(1, 5),
        GPXTrackPoint(1, 6),
        GPXTrackPoint(2, 6),
        GPXTrackPoint(2, 5),
        GPXTrackPoint(1, 5),
        GPXTrackPoint(1, 4),
        GPXTrackPoint(1, 3),
        GPXTrackPoint(1, 2),
    ]

    match_segment = GPXTrackSegment()
    match_segment.points = [
        GPXTrackPoint(1, 1),
        GPXTrackPoint(1, 2),
        GPXTrackPoint(1, 3),
    ]

    data = get_segment_overlap(
        base_segment,
        match_segment,
        distance(
            Position2D(latitude=1, longitude=1), Position2D(latitude=1, longitude=2)
        ),
        1,
        0,
        0.0,
    )

    assert len(data) == 2
    data[0].overlap = 1
    data[1].overlap = 2 / 3


@pytest.mark.parametrize(
    ("points", "allow_points", "exp"),
    [
        (
            [
                (0, True),
                (1, True),
                (2, True),
                (3, False),
                (4, False),
                (5, True),
                (6, True),
            ],
            0,
            [(0, 2), (5, 6)],
        ),
        (
            [
                (0, True),
                (1, True),
                (2, True),
                (3, False),
                (4, False),
                (5, True),
                (6, True),
            ],
            3,
            [(0, 6)],
        ),
        (
            [
                (0, True),
                (1, True),
                (2, True),
                (3, False),
                (4, False),
                (5, True),
                (6, True),
                (7, False),
                (8, False),
                (9, False),
                (10, False),
                (11, True),
                (12, True),
            ],
            3,
            [(0, 6), (11, 12)],
        ),
    ],
)
def test_extract_ranges(
    points: list[tuple[int, bool]], allow_points: int, exp: list[tuple[int, int]]
) -> None:
    assert _extract_ranges(points, allow_points) == exp

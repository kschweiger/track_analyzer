import math
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock

import gpxpy
import pandas as pd
import pytest
from gpxpy.gpx import GPXTrack

from gpx_track_analyzer.exceptions import (
    TrackInitializationException,
    TrackTransformationException,
)
from gpx_track_analyzer.model import SegmentOverview
from gpx_track_analyzer.track import FileTrack, PyTrack


def gen_track(points=None):
    gpx = gpxpy.gpx.GPX()

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    if points is None:
        point_values = [
            (2.1234, 5, 100, "2022-06-01T14:30:35+00:00"),
            (2.1235, 5, 105, "2022-06-01T14:30:40+00:00"),
            (2.1236, 5, 110, "2022-06-01T14:30:45+00:00"),
            (2.1237, 5, 115, "2022-06-01T14:30:50+00:00"),
            (2.1238, 5, 105, "2022-06-01T14:30:55+00:00"),
            (2.1239, 5, 100, "2022-06-01T14:31:00+00:00"),
            (2.1240, 5, 90, "2022-06-01T14:31:05+00:00"),
            (2.1241, 5, 100, "2022-06-01T14:31:10+00:00"),
        ]
    else:
        point_values = points

    for lat, long, ele, time in point_values:

        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                lat,
                long,
                elevation=ele,
                time=datetime.fromisoformat(time) if isinstance(time, str) else time,
            )
        )
    return gpx


def gen_segment_data(elevations: List[int]) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "latitude": [],
        "longitude": [],
        "elevation": [],
        "speed": [],
        "distance": [],
        "distance_2d": [],
        "cum_distance": [],
        "cum_distance_moving": [],
        "cum_distance_stopped": [],
        "moving": [],
    }
    prev_elevation = elevations[0]
    for i, elevation_value in enumerate(elevations):
        elevation_diff = abs(elevation_value - prev_elevation)
        prev_elevation = elevation_value
        data["latitude"].append(1)
        data["longitude"].append(1)
        data["elevation"].append(elevation_value)
        data["speed"].append(2.5 if i != 0 else None)
        data["distance"].append(
            math.sqrt(49 + elevation_diff * elevation_diff) if i != 0 else None
        )
        data["distance_2d"].append(7 if i != 0 else None)
        data["cum_distance"].append(None)  # Not important
        data["cum_distance_moving"].append(None)  # Not important
        data["cum_distance_stopped"].append(None)  # Not important
        data["moving"].append(True)  # Not important

    return data


@pytest.fixture()
def generate_mock_track():
    return gen_track(None)


def test_track(mocker, generate_mock_track):
    MockedFileTrack = FileTrack
    MockedFileTrack._get_pgx = MagicMock()
    MockedFileTrack._get_pgx.return_value = generate_mock_track

    track = MockedFileTrack("bogus_file_name.gpx")
    segment_overview = track.get_segment_overview(0)
    assert isinstance(segment_overview, SegmentOverview)


@pytest.mark.parametrize(
    ("points", "elevations", "time"),
    [
        ([(50, 50), (51, 51), (52, 52)], None, None),
        ([(50, 50), (51, 51), (52, 52)], [100, 200, 300], None),
        (
            [(50, 50), (51, 51), (52, 52)],
            None,
            [
                datetime(2023, 1, 1, 10),
                datetime(2023, 1, 1, 11),
                datetime(2023, 1, 1, 12),
            ],
        ),
        (
            [(50, 50), (51, 51), (52, 52)],
            [100, 200, 300],
            [
                datetime(2023, 1, 1, 10),
                datetime(2023, 1, 1, 11),
                datetime(2023, 1, 1, 12),
            ],
        ),
    ],
)
def test_py_track(points, elevations, time):
    track = PyTrack(points, elevations, time)

    assert isinstance(track.track, GPXTrack)

    data = track.get_segment_data()

    assert isinstance(data, pd.DataFrame)

    overview = track.get_segment_overview()

    assert isinstance(overview, SegmentOverview)


@pytest.mark.parametrize(
    ("points", "elevations", "time"),
    [
        ([(50, 50), (51, 51), (52, 52)], [100, 200], None),
        (
            [(50, 50), (51, 51), (52, 52)],
            None,
            [
                datetime(2023, 1, 1, 10),
                datetime(2023, 1, 1, 11),
            ],
        ),
    ],
)
def test_py_track_init_exceptions(points, elevations, time):
    with pytest.raises(TrackInitializationException):
        PyTrack(points, elevations, time)


def test_interpolate_linear_points_in_segment_lat_lng_only():
    # Distacne 2d: ~1000m
    track = PyTrack([(0, 0), (0.0089933, 0)], None, None)

    track.interpolate_points_in_segment(spacing=200)

    assert len(track.track.segments[0].points) == 6
    for point in track.track.segments[0].points:
        assert point.elevation is None
        assert point.time is None


def test_interpolate_linear_points_in_segment_no_interpolation():
    track = PyTrack([(0, 0), (0.0089933, 0)], None, None)

    track.interpolate_points_in_segment(spacing=2000)

    assert len(track.track.segments[0].points) == 2


def test_interpolate_linear_points_in_segment_lat_lng_ele():
    track = PyTrack([(0, 0), (0.0089933, 0)], [100, 200], None)

    track.interpolate_points_in_segment(spacing=200)

    assert len(track.track.segments[0].points) == 6
    for point in track.track.segments[0].points:
        assert point.elevation is not None
        assert point.time is None


def test_interpolate_linear_points_in_segment_lat_lng_ele_time():
    # Distacne 2d: ~1000m
    track = PyTrack(
        [(0, 0), (0.0089933, 0)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    track.interpolate_points_in_segment(spacing=200)

    assert len(track.track.segments[0].points) == 6
    for point in track.track.segments[0].points:
        assert point.elevation is not None
        assert point.time is not None


@pytest.mark.parametrize(
    ("points", "n_exp"),
    [
        ([(0, 0), (0.0089933, 0), (0.0010, 0)], 10),
        ([(0, 0), (0.0089933, 0), (0.0010, 0), (0.0011, 0)], 11),
    ],
)
def test_interpolate_linear_points_in_segment_multiple_points(points, n_exp):
    # Distacne 2d: ~1000m
    track = PyTrack(points, None, None)

    track.interpolate_points_in_segment(spacing=200)

    assert len(track.track.segments[0].points) == n_exp


@pytest.mark.parametrize(
    ("coords", "eles", "times"),
    [
        ([(1, 1), (2, 2)], None, None),
        ([(1, 1), (2, 2)], [100, 200], None),
        (
            [(1, 1), (2, 2)],
            [100, 200],
            [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
        ),
    ],
)
def test_get_point_data_in_segmnet(coords, eles, times):
    track = PyTrack(coords, eles, times)

    ret_coords, ret_eles, ret_times = track.get_point_data_in_segmnet(0)

    assert ret_coords == coords
    assert ret_eles == eles
    assert ret_times == times


def test_get_point_data_in_segment_exception_ele():
    track = PyTrack(
        [(1, 1), (2, 2)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    track.track.segments[0].points[1].elevation = None

    with pytest.raises(TrackTransformationException):
        track.get_point_data_in_segmnet()


def test_get_point_data_in_segment_exception_time():
    track = PyTrack(
        [(1, 1), (2, 2)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    track.track.segments[0].points[1].time = None

    with pytest.raises(TrackTransformationException):
        track.get_point_data_in_segmnet()


@pytest.mark.parametrize(
    ("elevations", "peaks", "valleys"),
    [
        ([100, 110, 120, 110, 120, 110, 100, 110], [], []),
        ([100, 120, 140, 150, 160, 180, 200], [6], [0]),
        ([200, 180, 160, 150, 140, 120, 100], [0], [6]),
        ([100, 130, 160, 200, 160, 130, 90], [3], [0, 6]),
        ([100, 130, 160, 200, 160, 130, 90, 120, 150, 180], [3, 9], [0, 6]),
        ([100, 110, 100, 130, 160, 200, 160, 130, 90], [5], [2, 8]),
        ([100, 110, 100, 130, 160, 200, 160, 130, 90, 100, 110, 100], [5], [2, 8]),
        (
            [100, 120, 140, 150, 160, 180, 200, 190, 210, 205, 200, 180, 160, 120],
            [6, 10],
            [0, 13],
        ),
    ],
)
def test_peaks_and_valleys(elevations, peaks, valleys):
    data = gen_segment_data(elevations)
    MockedFileTrack = FileTrack
    MockedFileTrack._get_pgx = MagicMock()
    MockedFileTrack._get_pgx.return_value = MagicMock()
    track = MockedFileTrack("bogus_file_name.gpx")
    track.get_segment_data = MagicMock()
    track.get_segment_data.return_value = pd.DataFrame(data)

    assert track.peaks == {}
    assert track.valleys == {}

    track.find_peaks_valleys(pd.DataFrame(data), 0)

    assert track.peaks[0] == peaks
    assert track.valleys[0] == valleys


@pytest.mark.parametrize(
    ("elevations", "ascents", "descents"),
    [
        ([100, 110, 120, 110, 120, 110, 100, 110], [], []),
        ([100, 120, 140, 150, 160, 180, 200], [(0, 6)], []),
        ([100, 130, 160, 200, 160, 130, 90], [(0, 3)], [(3, 6)]),
        ([100, 110, 100, 130, 160, 200, 160, 130, 90], [(2, 5)], [(5, 8)]),
        (
            [100, 110, 100, 130, 160, 200, 160, 130, 90, 100, 110, 100],
            [(2, 5)],
            [(5, 8)],
        ),
        (
            [100, 120, 140, 150, 160, 180, 200, 190, 210, 205, 200, 180, 160, 120],
            [(0, 6)],
            [(10, 13)],
        ),
    ],
)
def test_ascents_descents(elevations, ascents, descents):

    data = gen_segment_data(elevations)

    MockedFileTrack = FileTrack
    MockedFileTrack._get_pgx = MagicMock()
    MockedFileTrack._get_pgx.return_value = MagicMock()
    track = MockedFileTrack("bogus_file_name.gpx")
    track.get_segment_data = MagicMock()
    track.get_segment_data.return_value = pd.DataFrame(data)

    assert track.ascent_boundaries == {}
    assert track.descent_boundaries == {}

    track.find_ascents_descents(pd.DataFrame(data), n_segment=0)

    assert track.ascent_boundaries[0] == ascents
    assert track.descent_boundaries[0] == descents

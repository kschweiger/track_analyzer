import importlib.resources
from datetime import datetime
from unittest.mock import MagicMock

import gpxpy
import pandas as pd
import pytest
from gpxpy.gpx import GPXTrack, GPXTrackPoint

from tests import resources
from track_analyzer.exceptions import (
    TrackInitializationError,
    TrackTransformationError,
)
from track_analyzer.model import SegmentOverview
from track_analyzer.track import ByteTrack, GPXFileTrack, PyTrack, Track
from track_analyzer.utils import get_extension_value


@pytest.fixture()
def generate_mock_track():
    gpx = gpxpy.gpx.GPX()

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
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

    for lat, long, ele, isotime in point_values:
        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                lat,
                long,
                elevation=ele,
                time=datetime.fromisoformat(isotime),
            )
        )

    return gpx


def test_track(mocker, generate_mock_track):
    MockedFileTrack = GPXFileTrack  # noqa: N806
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
    with pytest.raises(TrackInitializationError):
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

    with pytest.raises(TrackTransformationError):
        track.get_point_data_in_segmnet()


def test_get_point_data_in_segment_exception_time():
    track = PyTrack(
        [(1, 1), (2, 2)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    track.track.segments[0].points[1].time = None

    with pytest.raises(TrackTransformationError):
        track.get_point_data_in_segmnet()


def test_get_closest_point():
    track = PyTrack(
        [(1, 1), (2, 2)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    point, distance, idx = track.get_closest_point(0, 1.1, 1.1)

    assert isinstance(point, GPXTrackPoint)
    assert isinstance(distance, float)
    assert isinstance(idx, int)

    assert idx == 0
    assert point.latitude == 1
    assert point.longitude == 1
    assert point.elevation == 100
    assert point.time == datetime(2023, 1, 1, 10, 0)


def test_overlap():
    resource_files = importlib.resources.files(resources)

    track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes()
    )

    match_track = ByteTrack(
        (resource_files / "Teilstueck_Schau_ins_land.gpx").read_bytes()
    )

    overlap_tracks = track.find_overlap_with_segment(0, match_track)

    assert len(overlap_tracks) == 1

    overlap_track, overlap_frac, inverse = overlap_tracks[0]

    assert isinstance(overlap_track, Track)
    assert overlap_frac == 1.0
    assert not inverse


def test_pytrack_extensions():
    track = PyTrack(
        [(1, 1)],
        [100],
        [datetime(2023, 1, 1, 10)],
        heartrate=[100],
        cadence=[80],
        power=[200],
    )

    point = track.track.segments[0].points[0]

    assert get_extension_value(point, "heartrate") == "100"
    assert get_extension_value(point, "cadence") == "80"
    assert get_extension_value(point, "power") == "200"


def test_pytrack_add_segement():
    track = PyTrack(
        [(1, 1)],
        [100],
        [datetime(2023, 1, 1, 10)],
        heartrate=[100],
        cadence=[80],
        power=[200],
    )

    assert len(track.track.segments) == 1

    track.add_segmeent(
        [(2, 2)],
        [200],
        [datetime(2023, 2, 1, 10)],
        heartrate=[60],
        cadence=[20],
        power=[100],
    )

    assert len(track.track.segments) == 2

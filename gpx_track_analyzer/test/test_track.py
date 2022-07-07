from datetime import datetime
from unittest.mock import MagicMock

import gpxpy
import pytest

from gpx_track_analyzer.model import SegmentOverview
from gpx_track_analyzer.track import FileTrack


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
    MockedFileTrack = FileTrack
    MockedFileTrack._get_pgx = MagicMock()
    MockedFileTrack._get_pgx.return_value = generate_mock_track

    track = MockedFileTrack("bogus_file_name.gpx")
    segment_overview = track.get_segment_overview(0)
    assert isinstance(segment_overview, SegmentOverview)

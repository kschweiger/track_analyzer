from datetime import datetime

import pytest

from geo_track_analyzer.exceptions import VisualizationSetupError
from geo_track_analyzer.track import PyTrack, Track
from geo_track_analyzer.utils.track import (
    extract_multiple_segment_data_for_plot,
    extract_segment_data_for_plot,
    extract_track_data_for_plot,
)


@pytest.mark.parametrize("pass_segments", [[1, 4], [1]])
def test_extract_multiple_segment_data_for_plot_errors(
    track_for_test_3_segments: Track, pass_segments: list[int]
) -> None:
    with pytest.raises(VisualizationSetupError):
        extract_multiple_segment_data_for_plot(
            track=track_for_test_3_segments,
            segments=pass_segments,
            kind="map-segments",
            require_elevation=["profile", "profile-slope"],
        )


def test_extract_segment_data_for_plot_no_ele_error() -> None:
    track = PyTrack(
        [
            (1.0001, 1.0001),
            (1.00012, 1.00012),
            (1.00014, 1.00014),
            (1.00016, 1.00016),
            (1.00018, 1.00018),
            (1.0002, 1.0002),
        ],
        None,
        [
            datetime(2023, 1, 1, 10),
            datetime(2023, 1, 1, 10, 0, 10),
            datetime(2023, 1, 1, 10, 0, 20),
            datetime(2023, 1, 1, 10, 0, 30),
            datetime(2023, 1, 1, 10, 0, 40),
            datetime(2023, 1, 1, 10, 0, 50),
        ],
    )
    with pytest.raises(VisualizationSetupError):
        extract_segment_data_for_plot(
            track=track, segment=0, kind="a", require_elevation=["a"]
        )


def test_extract_segment_data_for_plot_segment_plot_error(
    track_for_test_3_segments: Track,
) -> None:
    with pytest.raises(VisualizationSetupError):
        extract_segment_data_for_plot(
            track=track_for_test_3_segments,
            segment=0,
            kind="map-segments",
            require_elevation=["a"],
        )


def test_extract_track_data_for_plot_errors() -> None:
    track = PyTrack(
        [
            (1.0001, 1.0001),
            (1.00012, 1.00012),
            (1.00014, 1.00014),
            (1.00016, 1.00016),
            (1.00018, 1.00018),
            (1.0002, 1.0002),
        ],
        None,
        [
            datetime(2023, 1, 1, 10),
            datetime(2023, 1, 1, 10, 0, 10),
            datetime(2023, 1, 1, 10, 0, 20),
            datetime(2023, 1, 1, 10, 0, 30),
            datetime(2023, 1, 1, 10, 0, 40),
            datetime(2023, 1, 1, 10, 0, 50),
        ],
    )
    with pytest.raises(VisualizationSetupError):
        extract_track_data_for_plot(
            track=track,
            kind="profile",
            require_elevation=["profile", "profile-slope"],
        )

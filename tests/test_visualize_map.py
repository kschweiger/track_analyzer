from datetime import datetime

import plotly.graph_objects as go
import pytest

from track_analyzer.exceptions import VisualizationSetupError
from track_analyzer.track import PyTrack, Track
from track_analyzer.visualize.map import (
    plot_segments_on_map,
    plot_track_enriched_on_map,
    plot_track_line_on_map,
)


@pytest.fixture()
def track_for_test() -> Track:
    track = PyTrack(
        points=[
            (46.74025, 11.95624),
            (46.74027, 11.95587),
            (46.74013, 11.95575),
            (46.73946, 11.95588),
            (46.73904, 11.95627),
            (46.73852, 11.95609),
        ],
        elevations=[2248, 2247, 2244, 2245, 2252, 2256],
        times=[
            datetime(2023, 8, 1, 10),
            datetime(2023, 8, 1, 10, 1),
            datetime(2023, 8, 1, 10, 2),
            datetime(2023, 8, 1, 10, 3),
            datetime(2023, 8, 1, 10, 4),
            datetime(2023, 8, 1, 10, 5),
        ],
        heartrate=[100, 120, 125, 121, 125, 130],
        cadence=[80, 81, 79, 70, 60, 65],
        power=[150, 200, 200, 210, 240, 250],
    )

    track.add_segmeent(
        points=[
            (46.73861, 11.95697),
            (46.73862, 11.95755),
            (46.73878, 11.95778),
            (46.73910, 11.95763),
            (46.73930, 11.95715),
            (46.74021, 11.95627),
        ],
        elevations=[2263, 2268, 2270, 2269, 2266, 2248],
        times=[
            datetime(2023, 8, 1, 10, 6),
            datetime(2023, 8, 1, 10, 7),
            datetime(2023, 8, 1, 10, 8),
            datetime(2023, 8, 1, 10, 9),
            datetime(2023, 8, 1, 10, 9),
            datetime(2023, 8, 1, 10, 10),
        ],
        heartrate=[155, 160, 161, 150, 140, 143],
        cadence=[82, 83, 78, 71, 66, 69],
        power=[240, 230, 234, 220, 210, 200],
    )

    return track


def test_plot_track_line_on_map(track_for_test: Track) -> None:
    data = track_for_test.get_track_data()

    figure = plot_track_line_on_map(data)

    assert isinstance(figure, go.Figure)


@pytest.mark.parametrize(
    "enrich_with_column", ["elevation", "speed", "heartrate", "cadence", "power"]
)
def test_plot_track_enriched_on_map(
    track_for_test: Track, enrich_with_column: str
) -> None:
    data = track_for_test.get_track_data()

    figure = plot_track_enriched_on_map(
        data, enrich_with_column=enrich_with_column  # type: ignore
    )
    assert isinstance(figure, go.Figure)


def test_plot_track_enriched_on_map_overwrites(track_for_test: Track) -> None:
    data = track_for_test.get_track_data()

    figure = plot_track_enriched_on_map(
        data,
        enrich_with_column="heartrate",
        overwrite_color_gradient=("#000000", "#FFFFFF"),
        overwrite_unit_text="some other unit",
    )

    assert isinstance(figure, go.Figure)


def test_plot_track_enriched_on_map_setup_error(track_for_test: Track) -> None:
    data = track_for_test.get_track_data()

    data.heartrate = None

    with pytest.raises(VisualizationSetupError):
        plot_track_enriched_on_map(
            data,
            enrich_with_column="heartrate",
        )


def test_plot_track_enriched_on_map_with_nans(
    track_for_test: Track,
) -> None:
    data = track_for_test.get_track_data()
    data.loc[1, "heartrate"] = None

    figure = plot_track_enriched_on_map(data, enrich_with_column="heartrate")

    assert isinstance(figure, go.Figure)


@pytest.mark.parametrize("average_only", [True, False])
def test_plot_segments_on_map(track_for_test: Track, average_only: bool) -> None:
    data = track_for_test.get_track_data()

    figure = plot_segments_on_map(data, average_only=average_only)

    assert isinstance(figure, go.Figure)


def test_plot_segments_on_map_no_segment_col(track_for_test: Track) -> None:
    data = track_for_test.get_track_data().copy()
    with pytest.raises(VisualizationSetupError):
        plot_segments_on_map(data.drop("segment", axis=1))


def test_plot_segments_on_map_single_segment(track_for_test: Track) -> None:
    data = track_for_test.get_track_data().copy()
    data["segment"] = 0
    with pytest.raises(VisualizationSetupError):
        plot_segments_on_map(data)

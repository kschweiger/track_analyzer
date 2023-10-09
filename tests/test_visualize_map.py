import plotly.graph_objects as go
import pytest

from track_analyzer.exceptions import VisualizationSetupError
from track_analyzer.track import Track
from track_analyzer.visualize.map import (
    plot_segments_on_map,
    plot_track_enriched_on_map,
    plot_track_line_on_map,
)


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

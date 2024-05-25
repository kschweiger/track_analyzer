import importlib.resources
from typing import Literal

import pandas as pd
import plotly.graph_objects as go
import pytest

from geo_track_analyzer.visualize.summary import (
    plot_segment_box_summary,
    plot_segment_summary,
    plot_segment_zones,
    plot_track_zones,
)
from tests import resources


@pytest.fixture()
def summary_data() -> pd.DataFrame:
    resource_files = importlib.resources.files(resources)

    return pd.read_csv(resource_files / "summary_test_data.csv", sep=";").drop(  # type: ignore
        "Unnamed: 0", axis=1
    )


@pytest.mark.parametrize("use_zone_colors", [True, False])
@pytest.mark.parametrize("aggregate", ["time", "distance", "speed"])
def test_plot_track_zones(
    summary_data: pd.DataFrame,
    use_zone_colors: bool,
    aggregate: Literal["time", "distance", "speed"],
) -> None:
    fig = plot_track_zones(
        data=summary_data,
        metric="heartrate",
        aggregate=aggregate,
        use_zone_colors=use_zone_colors,
    )

    # fig.show()

    assert isinstance(fig, go.Figure)


@pytest.mark.parametrize(
    "colors",
    [None, ("#FF0000", "#00FF00"), ["#FF0000", "#00FF00", "#0000FF", "#FF00FF"]],
)
@pytest.mark.parametrize("aggregate", ["time", "distance", "speed"])
def test_plot_segment_zones(
    summary_data: pd.DataFrame,
    aggregate: Literal["time", "distance", "speed"],
    colors: None | tuple[str, str] | list[str],
) -> None:
    fig = plot_segment_zones(
        data=summary_data, metric="heartrate", aggregate=aggregate, bar_colors=colors
    )

    # fig.show()

    assert isinstance(fig, go.Figure)


@pytest.mark.parametrize(
    "aggregate", ["total_time", "total_distance", "avg_speed", "max_speed"]
)
def test_plot_segment_summary(
    summary_data: pd.DataFrame,
    aggregate: Literal["total_time", "total_distance", "avg_speed", "max_speed"],
) -> None:
    fig = plot_segment_summary(
        data=summary_data,
        aggregate=aggregate,
    )

    # fig.show()

    assert isinstance(fig, go.Figure)


@pytest.mark.parametrize("metric", ["heartrate", "speed", "elevation"])
def test_plot_segment_box_summary(
    summary_data: pd.DataFrame,
    metric: Literal["heartrate", "power", "cadence", "speed", "elevation"],
) -> None:
    fig = plot_segment_box_summary(
        data=summary_data,
        metric=metric,
    )
    # fig.show()

    assert isinstance(fig, go.Figure)

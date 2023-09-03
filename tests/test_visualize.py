import importlib.resources

import pandas as pd
import plotly.graph_objects as go
import pytest

from tests import resources
from track_analyzer.exceptions import VisualizationSetupError
from track_analyzer.track import ByteTrack, PyTrack
from track_analyzer.visualize import (
    get_slope_colors,
    plot_track_2d,
    plot_track_with_slope,
)


def test_get_slope_colors():
    colors = get_slope_colors("#0000FF", "#00FF00", "#00FF00", -5, 5)

    assert len(colors.keys()) == 11
    assert colors[-5] == "#0000FF"
    assert colors[0] == "#00FF00"
    assert colors[5] == "#00FF00"


def test_plot_track_with_slope():
    resource_files = importlib.resources.files(resources)

    test_track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes()
    )

    fig = plot_track_with_slope(test_track, 0)

    assert isinstance(fig, go.Figure)

    fig = plot_track_with_slope(test_track, 0, intervals=1)

    assert isinstance(fig, go.Figure)


@pytest.mark.parametrize(
    "flag",
    [{"include_heartrate": True}, {"include_cadence": True}, {"include_power": True}],
)
def test_2d_plot_w_extensions(flag):
    track = PyTrack(
        points=[(1, 1), (2, 2), (3, 3), (4, 4)],
        elevations=[100, 200, 220, 200],
        times=None,
        heartrate=[100, 80, 90, 70],
        cadence=[80, 70, 70, 60],
        power=[200, 300, 450, 500],
    )
    data = track.get_segment_data(0)
    fig = plot_track_2d(data, **flag)
    assert isinstance(fig, go.Figure)


@pytest.mark.parametrize(
    "combinations",
    [
        {"include_velocity": True, "include_heartrate": True},
        {"include_velocity": True, "include_heartrate": True, "include_cadence": True},
        {
            "include_velocity": True,
            "include_heartrate": True,
            "include_cadence": True,
            "include_power": True,
        },
    ],
)
def test_2d_plot_w_extensions_plot_mulitple_error(combinations):
    with pytest.raises(VisualizationSetupError):
        plot_track_2d(pd.DataFrame({}), **combinations)


@pytest.mark.parametrize(
    "flag",
    [{"include_heartrate": True}, {"include_cadence": True}, {"include_power": True}],
)
def test_2d_plot_w_extensions_plot_no_data_error(flag):
    track = PyTrack(
        points=[(1, 1), (2, 2), (3, 3), (4, 4)],
        elevations=[100, 200, 220, 200],
        times=None,
    )
    data = track.get_segment_data(0)
    with pytest.raises(VisualizationSetupError):
        plot_track_2d(data, **flag)

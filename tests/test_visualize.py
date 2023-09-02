import importlib.resources

import plotly.graph_objects as go

from tests import resources
from track_analyzer.track import ByteTrack
from track_analyzer.visualize import get_slope_colors, plot_track_with_slope


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

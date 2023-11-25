import importlib.resources

import plotly.graph_objects as go

from geo_track_analyzer.track import ByteTrack
from geo_track_analyzer.visualize.interactive import plot_track_3d
from tests import resources


def test_plot_track_3d() -> None:
    resource_files = importlib.resources.files(resources)

    test_track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes()
    )

    data = test_track.get_track_data().copy()

    figure = plot_track_3d(data)

    assert isinstance(figure, go.Figure)

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

from gpx_track_analyzer.utils import center_geolocation


def plot_track_2d(
    data: pd.DataFrame,
    include_velocity: bool = False,
    strict_data_selection: bool = False,
    height: Optional[int] = 600,
    width: Optional[int] = 1800,
) -> Figure:
    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot = data[mask]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=data_for_plot.cum_distance_moving,
            y=data_for_plot.elevation,
            mode="lines",
            name="Elevation [m]",
            fill="tozeroy",
        ),
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Elevation [m]",
        secondary_y=False,
        range=[
            data_for_plot.elevation.min() * 0.97,
            data_for_plot.elevation.max() * 1.05,
        ],
    )
    fig.update_xaxes(title_text="Distance [m]")
    if include_velocity:
        velocities = data_for_plot.apply(lambda c: c.speed * 3.6, axis=1)
        fig.add_trace(
            go.Scatter(
                x=data_for_plot.cum_distance_moving,
                y=velocities,
                mode="lines",
                name="Speed [km/h]",
                fill="tozeroy",
            ),
            secondary_y=True,
        )
        fig.update_yaxes(
            title_text="Velocity [km/h]",
            secondary_y=True,
            range=[0, velocities.max() * 2.1],
        )

    fig.update_layout(
        showlegend=False, autosize=False, margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    if height is not None:
        fig.update_layout(height=height)
    if width is not None:
        fig.update_layout(width=width)
    return fig


def plot_track_3d(data: pd.DataFrame, strict_data_selection: bool = False) -> Figure:
    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot = data[mask]

    fig = px.line_3d(data_for_plot, x="latitude", y="longitude", z="elevation")

    return fig


def plot_track_on_map(
    data: pd.DataFrame,
    zoom: int = 13,
    height: Optional[int] = None,
    width: Optional[int] = None,
) -> Figure:
    mask = data.moving

    center_lat, center_lon = center_geolocation(
        [(r["latitude"], r["longitude"]) for r in data[mask].to_dict("records")]
    )
    fig = px.line_mapbox(
        data[mask],
        lat="latitude",
        lon="longitude",
        zoom=zoom,
        center={"lon": center_lon, "lat": center_lat},
        height=height,
        width=width,
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 57, "t": 0, "l": 49, "b": 0})

    return fig


if __name__ == "__main__":
    import sys

    from gpx_track_analyzer.track import FileTrack

    file = sys.argv[1]

    track = FileTrack(file)
    data = track.get_segment_data(0)

    # fig = plot_track_2d(data, True)
    fig = plot_track_on_map(data)
    fig.show()

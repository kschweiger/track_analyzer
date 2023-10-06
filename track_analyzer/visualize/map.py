import logging
from typing import Literal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import Figure

from track_analyzer.utils import center_geolocation, get_color_gradient
from track_analyzer.visualize.constants import (
    COLOR_GRADIENTS,
    DEFAULT_COLOR_GRADIENT,
    ENRICH_UNITS,
)

logger = logging.getLogger(__name__)


def plot_track_line_on_map(
    data: pd.DataFrame,
    zoom: int = 13,
    height: None | int = None,
    width: None | int = None,
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


def plot_track_enriched_on_map(
    data: pd.DataFrame,
    enrich_with_column: Literal["elevation", "speed", "heartrate", "cadence", "power"],
    zoom: int = 13,
    height: None | int = None,
    width: None | int = None,
    overwrite_color_gradient: None | tuple[str, str] = None,
    overwrite_unit_text: None | str = None,
    cbar_ticks: int = 5,
) -> Figure:
    mask = data.moving

    plot_data = data[mask]

    center_lat, center_lon = center_geolocation(
        [(r["latitude"], r["longitude"]) for r in data[mask].to_dict("records")]
    )

    # ~~~~~~~~~~~~ Enrichment data ~~~~~~~~~~~~~~~~
    enrich_unit = (
        ENRICH_UNITS[enrich_with_column]
        if overwrite_unit_text is None
        else overwrite_unit_text
    )
    enrich_type = (
        int if enrich_with_column in ["heartrate", "cadence", "power"] else float
    )

    # ~~~~~~~~~~~ Generator colors for passed column ~~~~~~~~~~~~~~~~~
    color_column_values = plot_data[enrich_with_column]
    if enrich_with_column == "speed":
        color_column_values = color_column_values * 3.6
    diff_abs = color_column_values.max() - color_column_values.min()
    assert diff_abs > 0

    if overwrite_color_gradient:
        color_min, color_max = overwrite_color_gradient
    else:
        if enrich_with_column in COLOR_GRADIENTS.keys():
            color_min, color_max = COLOR_GRADIENTS[enrich_with_column]
        else:
            color_min, color_max = DEFAULT_COLOR_GRADIENT
    color_map = pd.Series(
        data=get_color_gradient(color_min, color_max, int(diff_abs) + 1),
        index=range(int(color_column_values.min()), int(color_column_values.max()) + 1),
    )

    def color_mapper(value: float) -> str:
        if value < color_map.index.start:
            return color_map.iloc[0]
        elif value > color_map.index.stop:
            return color_map.iloc[-1]
        else:
            return color_map.loc[int(value)]

    colors = color_column_values.apply(color_mapper).to_list()
    marker = go.scattermapbox.Marker(color=colors)

    # ~~~~~~~~~~~~~~~ Colorbar for the passed column ~~~~~~~~~~~~~~~~~~~~
    splits = 1 / (cbar_ticks - 1)
    factor = 0.0
    tick_vals = []
    tick_cols = []
    while factor <= 1:
        idx = int(diff_abs * factor)
        tick_vals.append(color_map.index[idx])
        tick_cols.append(color_map.iloc[idx])
        factor += splits

    colorbar_trace = go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            colorscale=color_map.to_list(),
            showscale=True,
            cmin=color_column_values.min(),
            cmax=color_column_values.max(),
            colorbar=dict(
                title=enrich_with_column.capitalize(),
                thickness=10,
                tickvals=tick_vals,
                ticktext=tick_vals,
                outlinewidth=0,
            ),
        ),
        hoverinfo="none",
    )

    # ~~~~~~~~~~~~~~~ Build figure ~~~~~~~~~~~~~~~~~~~
    fig = go.Figure(
        go.Scattermapbox(
            lat=plot_data["latitude"],
            lon=plot_data["longitude"],
            mode="markers",
            marker=marker,
            hovertemplate=f"{enrich_with_column.capitalize()}: "
            + "<b>%{text}</b> "
            + f"{enrich_unit} <br>"
            + "<b>Lat</b>: %{lat:4.6f}°<br>"
            + "<b>Lon</b>: %{lon:4.6f}°<br>",
            text=[enrich_type(v) for v in color_column_values.to_list()],
            name="",
        )
    )

    fig.add_trace(colorbar_trace)

    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(
        margin={"r": 57, "t": 5, "l": 49, "b": 5},
        mapbox={
            "style": "open-street-map",
            "zoom": zoom,
            "center": {"lon": center_lon, "lat": center_lat},
        },
        height=height,
        hovermode="closest",
        width=width,
        showlegend=False,
    )

    return fig

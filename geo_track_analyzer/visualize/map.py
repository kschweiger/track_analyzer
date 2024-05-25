import logging
from datetime import timedelta
from typing import Literal

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import Figure

from geo_track_analyzer.exceptions import VisualizationSetupError
from geo_track_analyzer.utils.base import (
    center_geolocation,
    format_timedelta,
)
from geo_track_analyzer.visualize.constants import (
    COLOR_GRADIENTS,
    DEFAULT_COLOR_GRADIENT,
    ENRICH_UNITS,
)
from geo_track_analyzer.visualize.utils import get_color_gradient

logger = logging.getLogger(__name__)


def plot_track_line_on_map(
    data: pd.DataFrame,
    *,
    zoom: int = 13,
    height: None | int = None,
    width: None | int = None,
    line_width: float = 2.5,
    map_style: str = "open-street-map",
    **kwargs,
) -> Figure:
    """
    Plot the track line on a map.

    :param data: DataFrame containing latitude and longitude data.
    :param zoom: Zoom level for the map, defaults to 13
    :param height: Height of the plot, defaults to None
    :param width: Width of the plot, defaults to None
    :param line_width: Width of the line on the map, defaults to 2.5
    :param map_style: Valid map_style for plotly mapbox_style, defaults to
        open-street-map
    :param kwargs: Additional keyword arguments.

    :return: Plotly Figure object.
    """
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
    fig.update_traces(
        line=dict(width=line_width),
    )
    fig.update_layout(
        mapbox_style=map_style,
        margin={"r": 57, "t": 0, "l": 49, "b": 0},
    )

    return fig


def plot_track_enriched_on_map(
    data: pd.DataFrame,
    *,
    enrich_with_column: Literal[
        "elevation", "speed", "heartrate", "cadence", "power"
    ] = "elevation",
    color_by_zone: bool = False,
    zoom: int = 13,
    height: None | int = None,
    width: None | int = None,
    overwrite_color_gradient: None | tuple[str, str] = None,
    overwrite_unit_text: None | str = None,
    cbar_ticks: int = 5,
    map_style: str = "open-street-map",
    **kwargs,
) -> Figure:
    """
    Plot the track line enriched with additional information (as z-axis) on a map.

    :param data: DataFrame containing track data.
    :param enrich_with_column: Column to enrich the track with, defaults to "elevation"
    :param color_by_zone: If True, track will be covered by Zones. Only available for
        enrich_with_column heartrate, cadence and power.
    :param zoom: Zoom level for the map, defaults to 13
    :param height: Height of the plot, defaults to None
    :param width: Width of the plot, defaults to None
    :param overwrite_color_gradient: Custom color gradient for the plot. Check
        track_analyzer.visualize.constants for defaults, defaults to None
    :param overwrite_unit_text: Custom unit text for the enrichment. Check
        track_analyzer.visualize.constants for defaults, defaults to None
    :param cbar_ticks: Number of color bar ticks, defaults to 5
    :param map_style: Valid map_style for plotly mapbox_style, defaults to
        open-street-map
    :param kwargs: Additional keyword arguments.
    :raises VisualizationSetupError: If no data is in passed enrich_with_column column
    :raises VisualizationSetupError: If color_by_zone is passed and enricht_with_column
        is unsupported or Zones are not set for the supported values
    :return: Plotly Figure object.
    """
    if color_by_zone and (
        (enrich_with_column not in ["heartrate", "cadence", "power"])
        or (f"{enrich_with_column}_zones" not in data.columns)
    ):
        raise VisualizationSetupError("Zone data is not provided in passed dataframe")

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

    # ~~~~~~~~~~~ Colors ~~~~~~~~~~~~~~~~~
    color_column_values = plot_data[enrich_with_column]

    if color_column_values.isna().all():
        raise VisualizationSetupError(
            f"Plotting not possible. No values for {enrich_with_column} in passed data."
        )

    if color_column_values.isna().any():
        logger.warning(
            "%s nan rows in %s. Dropping points",
            color_column_values.isna().sum(),
            enrich_with_column,
        )
        plot_data = plot_data[~color_column_values.isna()]
        color_column_values = color_column_values[~color_column_values.isna()]

    if enrich_with_column == "speed":
        color_column_values = color_column_values * 3.6
    diff_abs = color_column_values.max() - color_column_values.min()
    assert diff_abs > 0

    colorbar_trace = None
    # ~~~~~~~~~~~~~~~~ Color by Zone ~~~~~~~~~~~~~~~~~~~~~~~
    if color_by_zone:
        color_col = f"{enrich_with_column}_zone_colors"
        colors = plot_data[color_col]
        marker = go.scattermapbox.Marker(color=colors)
    # ~~~~~~~~~~~~~~~~ Generate color gradient from value ~~~~~~~~~~~~~~~
    else:
        if overwrite_color_gradient:
            color_min, color_max = overwrite_color_gradient
        else:
            if enrich_with_column in COLOR_GRADIENTS.keys():
                color_min, color_max = COLOR_GRADIENTS[enrich_with_column]
            else:
                color_min, color_max = DEFAULT_COLOR_GRADIENT
        color_map = pd.Series(
            data=get_color_gradient(color_min, color_max, round(diff_abs) + 1),
            index=range(
                round(color_column_values.min()), round(color_column_values.max()) + 1
            ),
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

    if colorbar_trace is not None:
        fig.add_trace(colorbar_trace)

    fig.update_layout(mapbox_style=map_style)
    fig.update_layout(
        margin={"r": 57, "t": 5, "l": 49, "b": 5},
        mapbox={
            "style": map_style,
            "zoom": zoom,
            "center": {"lon": center_lon, "lat": center_lat},
        },
        height=height,
        hovermode="closest",
        width=width,
        showlegend=False,
    )

    return fig


def plot_segments_on_map(
    data: pd.DataFrame,
    *,
    zoom: int = 13,
    height: None | int = None,
    width: None | int = None,
    line_width: float = 2.5,
    average_only: bool = True,
    map_style: str = "open-street-map",
    **kwargs,
) -> Figure:
    """
    Plot track line on map. Segments are displayed individually.

    :param data: DataFrame containing track segment data.
    :param zoom: Zoom level for the map, defaults to 13
    :param height: Height of the plot, defaults to None
    :param width: Width of the plot, defaults to None
    :param line_width: Width of the line on the map, defaults to 2.5
    :param average_only: Flag to display averages only, defaults to True
    :param map_style: Valid map_style for plotly mapbox_style, defaults to
        open-street-map
    :param kwargs: Additional keyword arguments.
    :raises VisualizationSetupError: If no segment information is contained in the data
    :raises VisualizationSetupError: If there are not two or more segments in the data

    :return: Plotly Figure object.
    """
    mask = data.moving

    plot_data = data[mask]

    if "segment" not in plot_data.columns:
        raise VisualizationSetupError(
            "Data has no **segment** in columns. Required for plot"
        )
    if len(plot_data.segment.unique()) < 2:
        raise VisualizationSetupError("Data does not have mulitple segments")

    center_lat, center_lon = center_geolocation(
        [(r["latitude"], r["longitude"]) for r in data[mask].to_dict("records")]
    )

    fig = go.Figure()
    for i_segment, frame in plot_data.groupby(by="segment"):
        mean_heartrate = frame.heartrate.agg("mean")
        min_heartrate = frame.heartrate.agg("min")
        max_heartrate = frame.heartrate.agg("max")

        mean_speed = frame.speed.agg("mean") * 3.6
        min_speed = frame.speed.agg("min") * 3.6
        max_speed = frame.speed.agg("max") * 3.6

        mean_power = frame.power.agg("mean")
        min_power = frame.power.agg("min")
        max_power = frame.power.agg("max")

        distance = frame.distance.sum() / 1000
        if frame.time.isna().all():
            total_time = None
        else:
            _total_time = frame.time.sum()  # in seconds
            total_time = timedelta(seconds=int(_total_time.astype(int)))
        min_elevation = frame.elevation.min()
        max_elevation = frame.elevation.max()

        text: str = (
            f"<b>Segment {i_segment}</b><br>"
            + f"<b>Distance</b>: {distance:.2f} km<br>"
        )
        if total_time is not None:
            text += f"<b>Time</b>: {format_timedelta(total_time)}<br>"

        text += (
            f"<b>Elevation</b>: &#8600; {min_elevation} m "
            + f"&#8599; {max_elevation} m<br>"
        )
        if not np.isnan(mean_speed):
            text += f"<b>Speed</b>: &#248; {mean_speed:.1f} "
            if not average_only:
                text += f" &#8600;{min_speed:.1f} &#8599;{max_speed:.1f} km/h <br>"
            text += " km/h <br>"
        if not np.isnan(mean_heartrate):
            text += f"<b>Heartrate</b>: &#248; {int(mean_heartrate)} "
            if not average_only:
                text += f"&#8600;{int(min_heartrate)} &#8599;{int(max_heartrate)}<br>"
            text += " bpm<br>"
        if not np.isnan(mean_power):
            text += f"<b>Power</b>: &#248; {mean_power:.1f} "
            if not average_only:
                text += f"&#8600;{min_power:.1f} &#8599;{max_power:.1f}<br>"
            text += " W<br>"

        fig.add_trace(
            go.Scattermapbox(
                lat=frame["latitude"],
                lon=frame["longitude"],
                mode="lines",
                hovertemplate="%{text} ",
                text=len(frame) * [text],
                line=dict(width=line_width),
                name="",
            )
        )

    fig.update_layout(
        margin={"r": 57, "t": 5, "l": 49, "b": 5},
        mapbox={
            "style": map_style,
            "zoom": zoom,
            "center": {"lon": center_lon, "lat": center_lat},
        },
        height=height,
        hovermode="closest",
        width=width,
        showlegend=False,
    )

    return fig


def plot_tracks_on_map(
    datas: list[pd.DataFrame],
    names: list[str],
    *,
    zoom: int = 13,
    height: None | int = None,
    width: None | int = None,
    line_width: float = 2.5,
    colors: None | list[str] = None,
    map_style: str = "open-street-map",
    **kwargs,
) -> Figure:
    fig = go.Figure()

    all_points = []
    for i, (data, name) in enumerate(zip(datas, names)):
        mask = data.moving
        plot_data = data[mask]

        mod_line: dict[str, float | str | int] = {"width": line_width}
        if colors is not None:
            mod_line["color"] = colors[i]

        fig.add_trace(
            go.Scattermapbox(
                lat=plot_data["latitude"],
                lon=plot_data["longitude"],
                mode="lines",
                # hovertemplate="%{text} ",
                # text=len(frame) * [text],
                line=mod_line,
                name=name,
            )
        )
        all_points.extend(
            [(r["latitude"], r["longitude"]) for r in data[mask].to_dict("records")]
        )

    center_lat, center_lon = center_geolocation(all_points)

    fig.update_layout(
        margin={"r": 57, "t": 5, "l": 49, "b": 5},
        mapbox={
            "style": map_style,
            "zoom": zoom,
            "center": {"lon": center_lon, "lat": center_lat},
        },
        height=height,
        hovermode="closest",
        width=width,
        showlegend=False,
    )

    return fig

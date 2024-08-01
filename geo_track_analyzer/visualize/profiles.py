import logging
from typing import Callable, Literal

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

from geo_track_analyzer.exceptions import VisualizationSetupError
from geo_track_analyzer.visualize.utils import get_slope_colors, group_dataframe

logger = logging.getLogger(__name__)


def _check_segment_availability(data: pd.DataFrame) -> bool:
    if "segment" not in data.columns:
        logger.warning(
            "Got show_segments but segments are not part of the data. "
            "Disabling segment borders."
        )
        return False
    if len(data.segment.unique()) == 1:
        logger.warning("Only a single segment in the data. Disabling segment borders.")
        return False
    return True


def _add_segment_borders(data: pd.DataFrame, fig: Figure, color: None | str) -> None:
    for idx, segment_border_idx in enumerate(
        data.index[data["segment"] != data["segment"].shift()].to_list()
    ):
        border_x = data.loc[segment_border_idx].cum_distance_moving
        fig.add_vline(
            x=border_x,
            # Hide line but keep abbitiation for first segment
            line_width=3 if idx > 0 else 0,
            line_dash="dash",
            line_color="darkslategray" if color is None else color,
            annotation_text=f"Segment {data.loc[segment_border_idx].segment}",
            annotation_borderpad=5,
        )


def _add_secondary(
    fig: Figure,
    data: pd.DataFrame,
    secondary: Literal["velocity", "heartrate", "cadence", "power", "speed"],
    split_by_zone: bool,
    min_zone_size: float,
) -> None:
    mode = "lines"
    fill: None | str = "tozeroy"
    y_range_max_factor = 1.2
    y_converter: Callable[[pd.Series], pd.Series] = lambda s: s.fillna(0).astype(int)
    if secondary == "velocity" or secondary == "speed":
        title = "Velocity [km/h]"
        y_range_max_factor = 2.1
        y_converter = lambda s: s * 3.6
        secondary = "speed"
    elif secondary == "heartrate":
        title = "Heart Rate [bpm]"
    elif secondary == "power":
        title = "Power [W]"
    elif secondary == "cadence":
        title = "Cadence [rpm]"
        fill = None
        mode = "markers"
    else:
        raise RuntimeError(
            "%s was passed for secondary. This is not supported" % secondary
        )

    if pd.isna(data[secondary]).all():
        raise VisualizationSetupError(
            f"Requested to plot{secondary} but data is (partially) missing in data"
        )

    if split_by_zone:
        _add_secondary_disonct(
            fig=fig,
            data=data,
            secondary=secondary,
            y_converter=y_converter,
            y_range_max_factor=y_range_max_factor,
            title=title,
            mode=mode,
            fill=fill,
            min_zone_size=min_zone_size,
        )
    else:
        y_data = y_converter(data[secondary])
        y_range = (0, y_data.max() * y_range_max_factor)

        _add_secondary_cont(
            fig=fig,
            x=data.cum_distance_moving,
            y=y_data,
            y_range=y_range,
            title=title,
            mode=mode,
            fill=fill,
        )


def _add_secondary_cont(
    fig: Figure,
    # data: pd.DataFrame,
    x: pd.Series,
    y: pd.Series,
    y_range: None | tuple[float, float],
    title: str,
    mode: str,
    fill: None | str,
    color: None | str = None,
    legend_group: None | str = None,
    show_legend: bool = False,
    y_title: None | str = None,
) -> None:
    scatter_kwargs = dict(
        x=x,
        y=y,
        mode=mode,
        name=title,
        legendgroup=legend_group,
        fill=fill,
        showlegend=show_legend,
    )
    if color is not None:
        scatter_kwargs["line_color"] = color
    fig.add_trace(
        go.Scatter(**scatter_kwargs),
        secondary_y=True,
    )
    fig.update_yaxes(
        title_text=title if y_title is None else y_title,
        secondary_y=True,
        range=y_range,
    )


def _add_secondary_disonct(
    fig: Figure,
    data: pd.DataFrame,
    secondary: str,
    y_converter: Callable[[pd.Series], pd.Series],
    y_range_max_factor: float,
    title: str,
    mode: str,
    fill: None | str,
    min_zone_size: float,
) -> None:
    if f"{secondary}_zones" not in data.columns:
        raise VisualizationSetupError("Zone data is not provided in passed dataframe")

    zone_data = group_dataframe(
        data, f"{secondary}_zones", int(len(data) * min_zone_size)
    )
    seen_group_names = []
    y_max = -99
    for data_ in zone_data[::-1]:
        group_name = data_[f"{secondary}_zones"].iloc[-1]

        y_data = y_converter(data_[secondary])
        y_max = max(y_max, y_data.max() * y_range_max_factor)

        _add_secondary_cont(
            fig=fig,
            x=data_.cum_distance_moving,
            y=y_data,
            y_range=None,
            title=group_name,
            mode=mode,
            fill=fill,
            color=data_[f"{secondary}_zone_colors"].iloc[-1],
            legend_group=group_name,
            show_legend=group_name not in seen_group_names,
            y_title=title,
        )
        if group_name not in seen_group_names:
            seen_group_names.append(group_name)

    fig.update_yaxes(
        range=(0, y_max),
        secondary_y=True,
    )


def plot_track_2d(
    data: pd.DataFrame,
    *,
    include_velocity: bool = False,
    include_heartrate: bool = False,
    include_cadence: bool = False,
    include_power: bool = False,
    show_segment_borders: bool = False,
    strict_data_selection: bool = False,
    height: None | int = 600,
    width: None | int = 1800,
    pois: None | list[tuple[float, float]] = None,
    color_elevation: None | str = None,
    color_additional_trace: None | str = None,
    color_poi: None | str = None,
    color_segment_border: None | str = None,
    slider: bool = False,
    split_by_zone: bool = False,
    min_zone_size: float = 0.0025,
    **kwargs,
) -> Figure:
    """Elevation profile of the track. May be enhanced with additional information like
    Velocity, Heartrate, Cadence, and Power.

    :param data: DataFrame containing track data
    :param include_velocity: Plot velocity as second y-axis, defaults to False
    :param include_heartrate: Plot heart rate as second y-axis, defaults to False
    :param include_cadence: Plot cadence as second y-axis, defaults to False
    :param include_power: Plot power as second y-axis, defaults to False
    :param show_segment_borders: If True show vertical lines between segments in track,
        defaults to False. If no segments are present in data, no error is raised.
    :param strict_data_selection: If True only included that passing the minimum speed
        requirements of the Track, defaults to False
    :param height: Height of the plot, defaults to 600
    :param width: Width of the plot, defaults to 1800
    :param pois: Optional lat/long coordingates to add to the plot as points of
        interest, defaults to None
    :param color_elevation: Color of the elevation as str interpretable by plotly,
        defaults to None
    :param color_additional_trace: Color of velocity/heartrate/cadence/power as str
        interpretable by plotly, defaults to None
    :param color_poi: Color of the pois as str interpretable by plotly, defaults to None
    :param color_segment_border: Color of the segment border lines as str interpretable
        by plotly, defaults to None
    :param slider: Should a slide be included in the plot to zoom into the x-axis,
        defaults to False
    :param split_by_zone: If True, and one for included_* flags is passed and Zones are
        set for the corresponding extension are set, the Zones will be colored
        according to the zone colors.
    :param min_zone_size: Minimum fraction of points required for a distinct zone, if
        split_by_Zone is passed.
    :raises VisualizationSetupError: If more than one of include_velocity,
        include_heartrate, include_cadence, or include_power was set the True
    :raises VisualizationSetupError: If elevation data is missing in the data
    :raises VisualizationSetupError: If the data requried for the additional data is
       missing
    :raises VisualizationSetupError: If split_by_zone is passed but Zones are not set

    :return: Plotly Figure object.
    """
    if split_by_zone:
        color_additional_trace = None
    if (
        sum(
            [
                int(include_velocity),
                int(include_heartrate),
                int(include_cadence),
                int(include_power),
            ]
        )
        > 1
    ):
        raise VisualizationSetupError(
            "Only one of include_velocity, include_heartrate, include_cadence, "
            "and include_power can be set to True"
        )
    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot: pd.DataFrame = data[mask].copy()  # type: ignore

    if show_segment_borders:
        show_segment_borders = _check_segment_availability(data_for_plot)

    if data_for_plot.elevation.isna().all():
        raise VisualizationSetupError("Can not plot profile w/o elevation information")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=data_for_plot.cum_distance_moving,
            y=data_for_plot.elevation,
            mode="lines",
            name="Elevation [m]",
            fill="tozeroy",
            text=[
                "<b>Lat</b>: {lat:4.6f}°<br><b>Lon</b>: {lon:4.6f}°<br>".format(
                    lon=rcrd["longitude"], lat=rcrd["latitude"]
                )
                for rcrd in data_for_plot.to_dict("records")
            ],
            hovertemplate="<b>Distance</b>: %{x:.1f} km <br><b>Elevation</b>: "
            + "%{y:.1f} m <br>%{text}<extra></extra>",
            showlegend=False,
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

    secondary = None
    if include_velocity:
        secondary = "velocity"
    if include_heartrate:
        secondary = "heartrate"
    if include_cadence:
        secondary = "cadence"
    if include_power:
        secondary = "power"

    if secondary is not None:
        _add_secondary(
            fig=fig,
            data=data_for_plot,
            secondary=secondary,
            split_by_zone=split_by_zone,
            min_zone_size=min_zone_size,
        )

    if pois is not None:
        for i_poi, poi in enumerate(pois):
            lat, lng = poi
            poi_data = data_for_plot[
                (data_for_plot.latitude == lat) & (data_for_plot.longitude == lng)
            ]
            if poi_data.empty:
                logger.warning("Could not find POI in data. Skipping")
                continue
            poi_x = poi_data.iloc[0].cum_distance_moving
            poi_y = poi_data.iloc[0].elevation

            fig.add_scatter(
                name=f"PIO {i_poi} @ {lat} / {lng}",
                x=[poi_x],
                y=[poi_y],
                mode="markers",
                marker=dict(
                    size=20,
                    color="MediumPurple" if color_poi is None else color_poi,
                    symbol="triangle-up",
                    standoff=10,
                    angle=180,
                ),
                showlegend=False,
            )

    if show_segment_borders:
        _add_segment_borders(data_for_plot, fig, color_segment_border)

    fig.update_layout(
        showlegend=split_by_zone,
        autosize=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    if height is not None:
        fig.update_layout(height=height)
    if width is not None:
        fig.update_layout(width=width)

    fig.update_xaxes(
        range=[
            data_for_plot.iloc[0].cum_distance_moving,
            data_for_plot.iloc[-1].cum_distance_moving,
        ]
    )

    if slider:
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
            )
        )

    if color_elevation is not None:
        fig.data[0].marker.color = color_elevation  # type: ignore
    if color_additional_trace is not None and any(
        [include_velocity, include_heartrate, include_cadence, include_power]
    ):
        fig.data[1].marker.color = color_additional_trace  # type: ignore

    return fig


def plot_track_with_slope(
    data: pd.DataFrame,
    *,
    slope_gradient_color: tuple[str, str, str] = ("#0000FF", "#00FF00", "#FF0000"),
    min_slope: int = -18,
    max_slope: int = 18,
    show_segment_borders: bool = False,
    height: None | int = 600,
    width: None | int = 1800,
    slider: bool = False,
    color_segment_border: None | str = None,
    **kwargs,
) -> Figure:
    """Elevation profile with slopes between points.

    :param data: DataFrame containing track data
    :param slope_gradient_color: Colors for the min, neutral, max slope values,
        defaults to ("#0000FF", "#00FF00", "#FF0000")
    :param min_slope: Minimum slope for the gradient also acts as floor for the
        displayed slope, defaults to -18
    :param max_slope: Maximum  slope for the gradient also acts as ceiling for the
        displayed slope, defaults to 18
    :param show_segment_borders: If True show vertical lines between segments in track,
        defaults to False. If no segments are present in data, no error is raised.
    :param height: Height of the plot, defaults to 600
    :param width: Width of the plot, defaults to 1800
    :param slider: Should a slide be included in the plot to zoom into the x-axis,
        defaults to False
    :param color_segment_border: Color of the segment border lines as str interpretable
        by plotly, defaults to None
    :raises VisualizationSetupError: If elevation data is missing in the data

    :return: Plotly Figure object
    """
    slope_color_map = get_slope_colors(
        *slope_gradient_color, max_slope=max_slope, min_slope=min_slope
    )

    data = data[data.moving].copy()  # type: ignore

    if data.elevation.isna().all():
        raise VisualizationSetupError("Can not plot profile w/o elevation information")

    if show_segment_borders:
        show_segment_borders = _check_segment_availability(data)

    elevations = data.elevation.to_list()
    diff_elevation = [0]
    for i, elevation in enumerate(elevations[1:]):
        diff_elevation.append(elevation - elevations[i])

    data["elevation_diff"] = diff_elevation

    def calc_slope(row: pd.Series) -> int:
        try:
            slope = round((row.elevation_diff / row.distance) * 100)
        except ZeroDivisionError:
            slope = 0

        if slope > max_slope:
            slope = max_slope
        elif slope < min_slope:
            slope = min_slope

        return slope

    data["slope"] = data.apply(lambda row: calc_slope(row), axis=1).astype(int)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.cum_distance_moving,
            y=data.elevation,
            mode="lines",
            name="Elevation [m]",
            fill="tozeroy",
        )
    )

    if slider:
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
            )
        )

    for i in range(len(data)):
        this_data = data.iloc[i : i + 2]
        if len(this_data) == 1:
            continue

        slope_val = this_data.iloc[1].slope

        color = slope_color_map[slope_val]
        max_distance: float = max(this_data.cum_distance_moving)
        fig.add_trace(
            go.Scatter(
                x=this_data.cum_distance_moving,
                y=this_data.elevation,
                mode="lines",
                name=f"Distance {max_distance/1000:.1f} km",
                fill="tozeroy",
                marker_color=color,
                hovertemplate=f"Slope: {slope_val} %",
            )
        )

    if show_segment_borders:
        _add_segment_borders(data, fig, color_segment_border)

    fig.update_layout(
        showlegend=False, autosize=False, margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    if height is not None:
        fig.update_layout(height=height)
    if width is not None:
        fig.update_layout(width=width)

    min_elevation: float = min(data.elevation)
    max_elevation: float = max(data.elevation)
    fig.update_yaxes(
        showspikes=True,
        spikemode="across",
        range=[min_elevation * 0.95, max_elevation * 1.05],
        title_text="Elevation [m]",
    )
    fig.update_xaxes(title_text="Distance [m]")

    return fig

import logging

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

from geo_track_analyzer.exceptions import VisualizationSetupError
from geo_track_analyzer.visualize.utils import get_slope_colors

logger = logging.getLogger(__name__)


def plot_track_2d(
    data: pd.DataFrame,
    *,
    include_velocity: bool = False,
    include_heartrate: bool = False,
    include_cadence: bool = False,
    include_power: bool = False,
    strict_data_selection: bool = False,
    height: None | int = 600,
    width: None | int = 1800,
    pois: None | list[tuple[float, float]] = None,
    color_elevation: None | str = None,
    color_additional_trace: None | str = None,
    color_poi: None | str = None,
    slider: bool = False,
    **kwargs,
) -> Figure:
    """Elevation profile of the track. May be enhanced with additional information like
    Velocity, Heartrate, Cadence, and Power.

    :param data: DataFrame containing track data
    :param include_velocity: Plot velocity as second y-axis, defaults to False
    :param include_heartrate: Plot heart rate as second y-axis, defaults to False
    :param include_cadence: Plot cadence as second y-axis, defaults to False
    :param include_power: Plot power as second y-axis, defaults to False
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
    :param slider: Should a slide be included in the plot to zoom into the x-axis,
        defaults to False
    :raises VisualizationSetupError: If more than one of include_velocity,
        include_heartrate, include_cadence, or include_power was set the True
    :raises VisualizationSetupError: If elevation data is missing in the data
    :raises VisualizationSetupError: If the data requried for the additional data is
       missing

    :return: Plotly Figure object.
    """
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

    data_for_plot = data[mask]

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

    y_data = None
    y_range = None
    title = None
    mode = "lines"
    fill: None | str = "tozeroy"
    if include_velocity:
        y_data = data_for_plot.apply(lambda c: c.speed * 3.6, axis=1)
        title = "Velocity [km/h]"
        y_range = [0, y_data.max() * 2.1]
    if include_heartrate:
        if pd.isna(data_for_plot.heartrate).all():
            raise VisualizationSetupError(
                "Requested to plot heart rate but no heart rate information available "
                "in data"
            )
        y_data = data_for_plot.heartrate.fillna(0).astype(int)
        title = "Heart Rate [bpm]"
        y_range = [0, y_data.max() * 1.2]
    if include_cadence:
        if pd.isna(data_for_plot.cadence).all():
            raise VisualizationSetupError(
                "Requested to plot cadence but no cadence information available in data"
            )
        y_data = data_for_plot.cadence.fillna(0).astype(int)
        title = "Cadence [rpm]"
        mode = "markers"
        fill = None
        y_range = [0, y_data.max() * 1.2]
    if include_power:
        if pd.isna(data_for_plot.power).all():
            raise VisualizationSetupError(
                "Requested to plot power but no power information available in data"
            )
        y_data = data_for_plot.power.fillna(0).astype(int)
        title = "Power [W]"
        y_range = [0, y_data.max() * 1.2]

    if y_data is not None:
        fig.add_trace(
            go.Scatter(
                x=data_for_plot.cum_distance_moving,
                y=y_data,
                mode=mode,
                name=title,
                fill=fill,
            ),
            secondary_y=True,
        )
        fig.update_yaxes(
            title_text=title,
            secondary_y=True,
            range=y_range,
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
            )

    fig.update_layout(
        showlegend=False, autosize=False, margin={"r": 0, "t": 0, "l": 0, "b": 0}
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
    height: None | int = 600,
    width: None | int = 1800,
    slider: bool = False,
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
    :param height: Height of the plot, defaults to 600
    :param width: Width of the plot, defaults to 1800
    :param slider: Should a slide be included in the plot to zoom into the x-axis,
        defaults to False
    :raises VisualizationSetupError: If elevation data is missing in the data

    :return: Plotly Figure object
    """
    slope_color_map = get_slope_colors(
        *slope_gradient_color, max_slope=max_slope, min_slope=min_slope
    )

    data = data[data.moving].copy()

    if data.elevation.isna().all():
        raise VisualizationSetupError("Can not plot profile w/o elevation information")

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

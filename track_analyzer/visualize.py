import logging
from typing import Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

from track_analyzer.exceptions import VisualizationSetupError
from track_analyzer.processing import (
    get_processed_segment_data,
    get_processed_track_data,
)
from track_analyzer.track import Track
from track_analyzer.utils import center_geolocation, get_color_gradient

logger = logging.getLogger(__name__)


def get_slope_colors(
    color_min: str,
    color_neutral: str,
    color_max: str,
    min_slope: int = -16,
    max_slope: int = 16,
) -> Dict[int, str]:
    """
    Generate a color gradient for the slope plots. The three passed colors are
    used for the MIN_SLOPE point, the 0 point and the MAX_SLOPE value respectively


    :param color_min: Color at the MIN_SLOPE value
    :param color_neutral: Color at 0
    :param color_max: Color at the MAX_SLOPE value
    :param min_slope: Minimum slope of the gradient, defaults to -16
    :param max_slope: Maximum slope of the gradient, defaults to 16
    :return: Dict mapping between slopes and colors
    """
    neg_points = list(range(min_slope, 1))
    pos_points = list(range(0, max_slope + 1))
    neg_colors = get_color_gradient(color_min, color_neutral, len(neg_points))
    pos_colors = get_color_gradient(color_neutral, color_max, len(pos_points))
    colors = {}
    colors.update({point: color for point, color in zip(neg_points, neg_colors)})
    colors.update({point: color for point, color in zip(pos_points, pos_colors)})
    return colors


def plot_track_2d(
    data: pd.DataFrame,
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
) -> Figure:
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


def plot_track_3d(data: pd.DataFrame, strict_data_selection: bool = False) -> Figure:
    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot = data[mask]

    return px.line_3d(data_for_plot, x="latitude", y="longitude", z="elevation")


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


def plot_track_with_slope(
    track: Track,
    n_segment: None | int,
    intervals: float = 200,
    slope_gradient_color: tuple[str, str, str] = ("#0000FF", "#00FF00", "#FF0000"),
    min_slope: int = -18,
    max_slope: int = 18,
    height: None | int = 600,
    width: None | int = 1800,
    slider: bool = False,
) -> None | Figure:
    slope_color_map = get_slope_colors(
        *slope_gradient_color, max_slope=max_slope, min_slope=min_slope
    )

    if n_segment is None:
        _track = track.track

        if not _track.has_elevations():
            logger.warning("Track has no elevation")
            return None

        if track.get_avg_pp_distance() >= intervals:
            logger.debug("Average pp distance larget than interval. Skipping reduction")
        else:
            _track = _track.clone()
            _track.reduce_points(intervals)

        _, _, _, _, data = get_processed_track_data(_track)

    else:
        segement = track.track.segments[n_segment]

        if not segement.has_elevations():
            logger.warning("Segement has no elevation")
            return None

        if track.get_avg_pp_distance_in_segment(n_segment) >= intervals:
            logger.debug("Average pp distance larget than interval. Skipping reduction")
        else:
            segement = track.track.segments[n_segment].clone()
            segement.reduce_points(intervals)

        _, _, _, _, data = get_processed_segment_data(segement)

    data = data[data.moving]

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


if __name__ == "__main__":
    import sys

    from track_analyzer.track import GPXFileTrack

    file = sys.argv[1]

    track = GPXFileTrack(file)
    data = track.get_segment_data(0)

    # fig = plot_track_2d(data, True)
    fig = plot_track_line_on_map(data)
    fig.show()

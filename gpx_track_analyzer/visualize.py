import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

from gpx_track_analyzer.processing import get_processed_segment_data
from gpx_track_analyzer.track import Track
from gpx_track_analyzer.utils import center_geolocation, get_color_gradient

logger = logging.getLogger(__name__)


def get_slope_colors(
    color_min: str, color_neutral: str, color_max: str, min_slope=-16, max_slope=16
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
    strict_data_selection: bool = False,
    height: Optional[int] = 600,
    width: Optional[int] = 1800,
    pois: Optional[List[Tuple[float, float]]] = None,
    color_elevation: Optional[str] = None,
    color_velocity: Optional[str] = None,
    color_poi: Optional[str] = None,
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

    if color_elevation is not None:
        fig.data[0].marker.color = color_elevation
    if color_velocity is not None and include_velocity:
        fig.data[1].marker.color = color_velocity

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


def plot_track_with_slope(
    track: Track,
    n_segment: int,
    intervals: float = 200,
    slope_gradient_color: tuple[str, str, str] = ("#0000FF", "#00FF00", "#FF0000"),
    min_slope: int = -18,
    max_slope: int = 18,
    height: Optional[int] = 600,
    width: Optional[int] = 1800,
) -> Optional[Figure]:
    slope_color_map = get_slope_colors(
        *slope_gradient_color, max_slope=max_slope, min_slope=min_slope
    )

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

    for i in range(len(data)):
        this_data = data.iloc[i : i + 2]
        if len(this_data) == 1:
            continue

        slope_val = this_data.iloc[1].slope

        color = slope_color_map[slope_val]
        fig.add_trace(
            go.Scatter(
                x=this_data.cum_distance_moving,
                y=this_data.elevation,
                mode="lines",
                name=f"Distance {max(this_data.cum_distance_moving)/1000:.1f} km",
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
    fig.update_yaxes(
        showspikes=True,
        spikemode="across",
        range=[min(data.elevation) * 0.9, max(data.elevation) * 1.1],
    )

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

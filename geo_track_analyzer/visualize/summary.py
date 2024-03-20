from typing import Literal

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objs import Figure

from geo_track_analyzer.exceptions import VisualizationSetupError
from geo_track_analyzer.visualize.constants import DEFAULT_BAR_COLORS, ENRICH_UNITS


def _preprocess_data(
    data: pd.DataFrame,
    metric: Literal["heartrate", "power", "cadence"],
    strict_data_selection: bool,
) -> pd.DataFrame:
    if metric not in data.columns:
        raise VisualizationSetupError("Metric %s not part of the passed data" % metric)

    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot = data[mask]

    if f"{metric}_zones" not in data_for_plot.columns:
        raise VisualizationSetupError("Zone data is not provided in passed dataframe")

    if pd.isna(data_for_plot[metric]).all():
        raise VisualizationSetupError(
            "Requested to plot %s but information is not available in data" % metric
        )

    return data_for_plot


def _aggregate_zone_data(
    data: pd.DataFrame,
    metric: Literal["heartrate", "power", "cadence"],
    aggregate: Literal["time", "distance"],
) -> tuple[pd.DataFrame, str, str]:
    bin_data = data.groupby(f"{metric}_zones")[aggregate].agg("sum").reset_index()
    if aggregate == "time":
        bin_data["time"] = pd.to_datetime(bin_data["time"].astype(int), unit="s")
        y_title = "Duration"
        tickformat = "%H:%M:%S"
    elif aggregate == "distance":
        bin_data["distance"] = bin_data["distance"] / 1000
        y_title = "Distance [km]"
        tickformat = ""
    else:
        raise NotImplementedError(f"Aggregation {aggregate} not supported")

    return bin_data, y_title, tickformat


def get_segmnet_ids(data: pd.DataFrame, segments: None | list[int]) -> list[int]:
    if segments is None:
        return sorted(data.segment.unique())
    else:
        if not all([s in data.segment.unique() for s in segments]):
            raise VisualizationSetupError(
                f"Not all passed segments are available in data. Passed {segments} "
                f"with {data.segment.unique()} in data."
            )
        return segments


def plot_track_zones(
    data: pd.DataFrame,
    metric: Literal["heartrate", "power", "cadence"],
    aggregate: Literal["time", "distance"],
    *,
    height: None | int = 600,
    width: None | int = 1200,
    strict_data_selection: bool = False,
) -> Figure:
    data_for_plot = _preprocess_data(data, metric, strict_data_selection)

    bin_data, y_title, tickformat = _aggregate_zone_data(
        data_for_plot, metric, aggregate
    )

    fig = go.Figure(
        go.Bar(x=bin_data[f"{metric}_zones"], y=bin_data[aggregate], hoverinfo="skip"),
    )

    for i, rcrd in enumerate(bin_data.to_dict("records")):
        kwargs = dict(
            x=i,
            showarrow=False,
            yshift=10,
        )
        if aggregate == "time":
            kwargs.update(
                dict(
                    y=rcrd["time"],
                    text=rcrd["time"].time().isoformat(),
                )
            )
        elif aggregate == "distance":
            kwargs.update(
                dict(
                    y=rcrd["distance"],
                    text=f"{rcrd['distance']:.2f} km",
                )
            )
        fig.add_annotation(**kwargs)

    fig.update_layout(
        title=f"{aggregate.capitalize()} in {metric.capitalize()} zones",
        yaxis=dict(tickformat=tickformat, title=y_title),
        bargap=0.0,
    )

    if height is not None:
        fig.update_layout(height=height)
    if width is not None:
        fig.update_layout(width=width)

    return fig


def plot_segment_zones(
    data: pd.DataFrame,
    metric: Literal["heartrate", "power", "cadence"],
    aggregate: Literal["time", "distance"],
    *,
    segments: None | list[int] = None,
    height: None | int = 600,
    width: None | int = 1200,
    strict_data_selection: bool = False,
) -> Figure:
    if "segment" not in data.columns:
        raise VisualizationSetupError(
            "Data has no **segment** in columns. Required for plot"
        )
    data_for_plot = _preprocess_data(data, metric, strict_data_selection)

    fig = go.Figure()

    for segment in get_segmnet_ids(data_for_plot, segments):
        _data_for_plot = data_for_plot[data_for_plot.segment == segment]
        bin_data, y_title, tickformat = _aggregate_zone_data(
            _data_for_plot, metric, aggregate
        )

        hovertext = []
        for rcrd in bin_data.to_dict("records"):
            if aggregate == "time":
                hovertext.append(rcrd["time"].time().isoformat())

            elif aggregate == "distance":
                hovertext.append(f"{rcrd['distance']:.2f} km")

        fig.add_trace(
            go.Bar(
                x=bin_data[f"{metric}_zones"],
                y=bin_data[aggregate],
                name=f"Segment {segment}",
                hovertext=hovertext,
                hovertemplate="%{hovertext}<extra></extra>",
            ),
        )

    fig.update_layout(
        title=f"{aggregate.capitalize()} in {metric.capitalize()} zones",
        yaxis=dict(tickformat=tickformat, title=y_title),
    )

    if height is not None:
        fig.update_layout(height=height)
    if width is not None:
        fig.update_layout(width=width)

    return fig


def plot_segment_summary(
    data: pd.DataFrame,
    aggregate: Literal["total_time", "total_distance", "avg_speed", "max_speed"],
    *,
    colors: None | tuple[str, str] = None,
    segments: None | list[int] = None,
    height: None | int = 600,
    width: None | int = 1200,
    strict_data_selection: bool = False,
) -> Figure:
    if "segment" not in data.columns:
        raise VisualizationSetupError(
            "Data has no **segment** in columns. Required for plot"
        )

    if colors is None:
        colors = DEFAULT_BAR_COLORS
    col_a, col_b = colors

    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot = data[mask]

    fig = go.Figure()

    _data_for_plot = data_for_plot[
        data_for_plot.segment.isin(get_segmnet_ids(data_for_plot, segments))
    ]

    if aggregate == "avg_speed":
        bin_data = _data_for_plot.groupby("segment").speed.agg("mean") * 3.6
        y_title = "Average velocity [km/h]"
        tickformat = ""
        hover_map_func = lambda v: str(f"{v:.2f} km/h")
    elif aggregate == "max_speed":
        bin_data = _data_for_plot.groupby("segment").speed.agg("max") * 3.6
        y_title = "Maximum velocity [km/h]"
        tickformat = ""
        hover_map_func = lambda v: str(f"{v:.2f} km/h")
    elif aggregate == "total_distance":
        bin_data = _data_for_plot.groupby("segment").distance.agg("sum") / 1000
        y_title = "Distance [km]"
        tickformat = ""
        hover_map_func = lambda v: str(f"{v:.2f} km")
    elif aggregate == "total_time":
        bin_data = pd.to_datetime(
            _data_for_plot.groupby("segment").time.agg("sum"), unit="s"
        )
        y_title = "Duration"
        tickformat = "%H:%M:%S"
        hover_map_func = lambda dt: str(dt.time())

    fig.add_trace(
        go.Bar(
            x=[f"Segment {idx}" for idx in bin_data.index.to_list()],
            y=bin_data.to_list(),
            marker_color=[col_a if i % 2 == 0 else col_b for i in range(len(bin_data))],
            hovertext=list(map(hover_map_func, bin_data.to_list())),
            hovertemplate="%{hovertext}<extra></extra>",
        ),
    )

    fig.update_layout(
        yaxis=dict(tickformat=tickformat, title=y_title),
        bargap=0.0,
    )

    if height is not None:
        fig.update_layout(height=height)
    if width is not None:
        fig.update_layout(width=width)

    return fig


def plot_segment_box_summary(
    data: pd.DataFrame,
    metric: Literal["heartrate", "power", "cadence", "speed"],
    *,
    colors: None | tuple[str, str] = None,
    segments: None | list[int] = None,
    height: None | int = 600,
    width: None | int = 1200,
    strict_data_selection: bool = False,
) -> Figure:
    if "segment" not in data.columns:
        raise VisualizationSetupError(
            "Data has no **segment** in columns. Required for plot"
        )

    if metric not in data.columns:
        raise VisualizationSetupError("Metric %s not part of the passed data" % metric)

    if colors is None:
        colors = DEFAULT_BAR_COLORS
    col_a, col_b = colors

    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot = data[mask]

    fig = go.Figure()

    for i, segment in enumerate(get_segmnet_ids(data_for_plot, segments)):
        _data_for_plot = data_for_plot[data_for_plot.segment == segment]

        if metric == "speed":
            box_data = _data_for_plot["speed"] * 3.6
        else:
            box_data = _data_for_plot[metric]

        fig.add_trace(
            go.Box(
                y=box_data,
                name=f"Segment {segment}",
                boxpoints=False,
                line_color=col_a if i % 2 == 0 else col_b,
                marker_color=col_a if i % 2 == 0 else col_b,
            )
        )
    if height is not None:
        fig.update_layout(height=height)
    if width is not None:
        fig.update_layout(width=width)

    fig.update_layout(
        yaxis=dict(title=f"{metric.capitalize()} {ENRICH_UNITS[metric]}"),
        showlegend=False,
    )

    return fig

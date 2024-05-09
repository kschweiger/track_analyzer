from typing import Any, Literal

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import make_colorscale, sample_colorscale
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
    aggregate: Literal["time", "distance", "speed"],
    aggregation_method: Literal["sum", "mean"],
) -> tuple[pd.DataFrame, str, str]:
    group = data.groupby(f"{metric}_zones")
    bin_data = group[aggregate].agg(aggregation_method).reset_index()
    if aggregate == "time":
        bin_data["time"] = pd.to_datetime(bin_data["time"].astype(int), unit="s")
        y_title = "duration"
        tickformat = "%H:%M:%S"
    elif aggregate == "distance":
        bin_data["distance"] = bin_data["distance"] / 1000
        y_title = "distance [km]"
        tickformat = ""
    elif aggregate == "speed":
        bin_data["speed"] = bin_data["speed"] * 3.6
        y_title = "velocity [km/h]"
        tickformat = ""
    else:
        raise NotImplementedError(f"Aggregation {aggregate} not supported")

    if aggregation_method == "sum":
        y_title = f"Total {y_title}"
    elif aggregation_method == "mean":
        y_title = f"Average {y_title}"

    bin_data["colors"] = group[f"{metric}_zone_colors"].first().to_numpy()

    return bin_data, y_title, tickformat


def plot_track_zones(
    data: pd.DataFrame,
    metric: Literal["heartrate", "power", "cadence"],
    aggregate: Literal["time", "distance", "speed"],
    *,
    use_zone_colors: bool = False,
    height: None | int = 600,
    width: None | int = 1200,
    strict_data_selection: bool = False,
) -> Figure:
    """Aggregate a value per zone defined for heartrate, power, or cadence.

    :param data: DataFrame containing track and zone data
    :param metric: One of "heartrate", "cadence", or "power"
    :param aggregate: Value to aggregate. Supported values are (total) "time",
        "distance",  and (average) speed in a certain zone
    :param use_zone_colors: If True, use distinct colors per zone (either set by the
        zone object or a default defined by the package). Otherwise alternating colors
        will be used, defaults to False.
    :param height: Height of the plot, defaults to 600
    :param width: Width of the plot, defaults to 1200
    :param strict_data_selection: If True only included that passing the minimum speed
        requirements of the Track, defaults to False
    :raises VisualizationSetupError: Is raised if metric is not avaialable in the data

    :return: Plotly Figure object
    """
    data_for_plot = _preprocess_data(data, metric, strict_data_selection)

    bin_data, y_title, tickformat = _aggregate_zone_data(
        data_for_plot,
        metric,
        aggregate,
        aggregation_method="mean" if aggregate == "speed" else "sum",
    )

    if use_zone_colors:
        colors = bin_data.colors
    else:
        col_a, col_b = DEFAULT_BAR_COLORS
        colors = []
        for i in range(len(bin_data)):
            colors.append(col_a if i % 2 == 0 else col_b)

    fig = go.Figure(
        go.Bar(
            x=bin_data[f"{metric}_zones"],
            y=bin_data[aggregate],
            marker_color=colors,
            hoverinfo="skip",
        ),
    )

    for i, rcrd in enumerate(bin_data.to_dict("records")):
        kwargs: dict[str, Any] = dict(
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
        elif aggregate == "speed":
            kwargs.update(
                dict(
                    y=rcrd["speed"],
                    text=f"{rcrd['speed']:.2f} km/h",
                )
            )
        else:
            raise NotImplementedError(f"Aggregate {aggregate} is not implemented")

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
    aggregate: Literal["time", "distance", "speed"],
    *,
    bar_colors: None | tuple[str, str] | list[str] = None,
    height: None | int = 600,
    width: None | int = 1200,
    strict_data_selection: bool = False,
) -> Figure:
    """Aggregate a value per zone defined for heartrate, power, or cadence, split into
    segments available in data.

    :param data: DataFrame containing track and zone data
    :param metric: One of heartrate, cadence, or power
    :param aggregate: Value to aggregate. Supported values are (total) "time",
        "distance",  and (average) speed in a certain zone
    :param bar_colors: Overwrite the default colors for the bar. If a tuple of two
        colors is passed, a colorscale will be generated based on these values and
        colors for segments will be picked from this scale. Furthermore, a list of
        colors can be passed that must at least be as long as the number of segments in
        the data
    :param height: Height of the plot, defaults to 600
    :param width: Width of the plot, defaults to 1200
    :param strict_data_selection: If True only included that passing the minimum speed
        requirements of the Track, defaults to False
    :raises VisualizationSetupError: Is raised if metric is not avaialable in the data
    :raises VisualizationSetupError: Is raised if no segment information is available in
        the data

    :return: Plotly Figure object
    """
    if "segment" not in data.columns:
        raise VisualizationSetupError(
            "Data has no **segment** in columns. Required for plot"
        )
    data_for_plot = _preprocess_data(data, metric, strict_data_selection)

    fig = go.Figure()

    plot_segments = data_for_plot.segment.unique()

    if isinstance(bar_colors, list):
        if len(plot_segments) > len(bar_colors):
            raise VisualizationSetupError(
                "If a list of colors is passed, it must be at least same lenght as the "
                "segments in the data"
            )
        colors = bar_colors[0 : len(plot_segments)]
    else:
        colors = sample_colorscale(
            make_colorscale(DEFAULT_BAR_COLORS if bar_colors is None else bar_colors),
            len(plot_segments),
        )

    for color, segment in zip(colors, plot_segments):
        _data_for_plot = data_for_plot[data_for_plot.segment == segment]
        bin_data, y_title, tickformat = _aggregate_zone_data(
            _data_for_plot,
            metric,
            aggregate,
            aggregation_method="mean" if aggregate == "speed" else "sum",
        )

        hovertext = []
        for rcrd in bin_data.to_dict("records"):
            if aggregate == "time":
                hovertext.append(rcrd["time"].time().isoformat())

            elif aggregate == "distance":
                hovertext.append(f"{rcrd['distance']:.2f} km")

            elif aggregate == "speed":
                hovertext.append(f"{rcrd['speed']:.2f} km/h")

        fig.add_trace(
            go.Bar(
                x=bin_data[f"{metric}_zones"],
                y=bin_data[aggregate],
                name=f"Segment {segment}",
                marker_color=color,
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
    height: None | int = 600,
    width: None | int = 1200,
    strict_data_selection: bool = False,
) -> Figure:
    """_summary_

    :param data: DataFrame containing track and zone data
    :param aggregate: Value to aggregate. Supported values are "total_time",
        "total_distance", "avg_speed", and "max_speed"
    :param colors: Overwrite the default alternating colors, defaults to None
    :param height: Height of the plot, defaults to 600
    :param width: Width of the plot, defaults to 1200
    :param strict_data_selection: If True only included that passing the minimum speed
        requirements of the Track, defaults to False
    :raises VisualizationSetupError: Is raised if no segment information is available in
        the data

    :return: Plotly Figure object
    """
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

    _data_for_plot = data[mask]

    fig = go.Figure()

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
    else:
        raise NotImplementedError(f"Aggregate {aggregate} is not implemented")

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
    metric: Literal["heartrate", "power", "cadence", "speed", "elevation"],
    *,
    colors: None | tuple[str, str] = None,
    height: None | int = 600,
    width: None | int = 1200,
    strict_data_selection: bool = False,
) -> Figure:
    """Show the metric as boxplot for each segment in the data.

    :param data: DataFrame containing track and zone data
    :param metric: One of "heartrate", "cadence", "power", or "speed"
    :param colors: Overwrite the default alternating colors, defaults to None
    :param height: Height of the plot, defaults to 600
    :param width: Width of the plot, defaults to 1200
    :param strict_data_selection: If True only included that passing the minimum speed
        requirements of the Track, defaults to False
    :raises VisualizationSetupError: Is raised if metric is not avaialable in the data
    :raises VisualizationSetupError: Is raised if no segment information is available in
        the data

    :return: Plotly Figure object
    """
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

    for i, segment in enumerate(data_for_plot.segment.unique()):
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

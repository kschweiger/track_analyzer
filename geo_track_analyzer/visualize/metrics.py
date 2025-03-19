import logging
import warnings
from enum import StrEnum, auto
from typing import Annotated, Callable

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

from geo_track_analyzer.exceptions import (
    VisualizationSetupError,
    VisualizationSetupWarning,
)
from geo_track_analyzer.visualize.utils import group_dataframe

from .constants import ENRICH_UNITS

logger = logging.getLogger(__name__)


class PlotMetric(StrEnum):
    ELEVATION = auto()
    HEARTRATE = auto()
    POWER = auto()
    CADENCE = auto()
    SPEED = auto()


class PlotBase(StrEnum):
    DISTANCE = "cum_distance_moving"
    DURATION = "cum_time_moving"


METRICS_WITH_ZONES = [PlotMetric.CADENCE, PlotMetric.HEARTRATE, PlotMetric.POWER]


def _add_scatter_cont(
    fig: Figure,
    x: pd.Series,
    y: pd.Series,
    y_range: None | tuple[float, float],
    title: str,
    mode: str,
    fill: None | str = None,
    color: None | str = None,
    legend_group: None | str = None,
    show_legend: bool = False,
    y_title: None | str = None,
    is_secondary: bool = False,
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
        secondary_y=is_secondary,
    )
    fig.update_yaxes(
        title_text=title if y_title is None else y_title,
        secondary_y=is_secondary,
        range=y_range,
    )


def _add_scatter_disonct(
    fig: Figure,
    data: pd.DataFrame,
    metric: str,
    y_converter: Callable[[pd.Series], pd.Series],
    y_range_max_factor: float,
    title: str,
    mode: str,
    fill: None | str = None,
    min_zone_size: float = 0.0025,
    is_secondary: bool = False,
    y_range_min_factor: float = 0,
) -> None:
    if f"{metric}_zones" not in data.columns:
        raise VisualizationSetupError("Zone data is not provided in passed dataframe")

    zone_data = group_dataframe(data, f"{metric}_zones", int(len(data) * min_zone_size))
    seen_group_names = []
    y_max = -99
    y_min = 99_999
    for data_ in zone_data[::-1]:
        group_name = data_[f"{metric}_zones"].iloc[-1]

        y_data = y_converter(data_[metric])
        y_max = max(y_max, y_data.max() * y_range_max_factor)
        y_min = min(y_min, y_data.min() * y_range_min_factor)
        _add_scatter_cont(
            fig=fig,
            x=data_.cum_distance_moving,
            y=y_data,
            y_range=None,
            title=group_name,
            mode=mode,
            fill=fill,
            color=data_[f"{metric}_zone_colors"].iloc[-1],
            legend_group=group_name,
            show_legend=group_name not in seen_group_names,
            y_title=title,
        )
        if group_name not in seen_group_names:
            seen_group_names.append(group_name)

    fig.update_yaxes(
        range=(y_min, y_max),
        secondary_y=is_secondary,
    )


def plot_metrics(
    data: pd.DataFrame,
    *,
    metrics: Annotated[list[PlotMetric], "Unique values"],
    base: PlotBase = PlotBase.DISTANCE,
    strict_data_selection: bool = False,
    height: int | None = 600,
    width: int | None = 1800,
    slider: bool = False,
    colors: list[str] | None = None,
    add_zones: bool = False,
) -> Figure:
    assert len(metrics) == len(set(metrics))

    if colors is None:
        _colors = [None for _ in metrics]
    else:
        if not len(colors) >= len(metrics):
            raise VisualizationSetupError(
                "Colors have been passed but at least "
                "the same number as metrics is required"
            )
        _colors = colors

    set_secondary = [False, True] if len(metrics) == 2 else [False for _ in metrics]
    if add_zones:
        zone_metrics = [m for m in metrics if m in METRICS_WITH_ZONES]
        if len(zone_metrics) == 0:
            add_zones = False
        elif len(zone_metrics) > 1:
            warnings.warn(
                VisualizationSetupWarning(
                    "Only one metric with zone is supported. Disabling zones"
                )
            )
            add_zones = False
        else:
            logger.debug("Adding zones for: %s", zone_metrics[0])
            # Make sure the zone metric is first
            _metrics = [zone_metrics[0]] + [m for m in metrics if m != zone_metrics[0]]
            _colors = [_colors[metrics.index(m)] for m in _metrics]
            metrics = _metrics
            set_secondary = [False] + [True for i in range(len(metrics) - 1)]

    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot: pd.DataFrame = data[mask].copy()  # type: ignore

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if base == PlotBase.DISTANCE:
        x_data = data_for_plot[base]
    else:
        x_data = pd.to_timedelta(data_for_plot[base], unit="s") + pd.Timestamp(
            "1970/01/01"
        )

    y_max = -99
    y_min = 99_999
    for metric, secondary, color in zip(metrics, set_secondary, _colors):
        if data_for_plot[metric].isna().all():
            if len(metrics) == 1:
                raise VisualizationSetupError(f"Cannot plot {metric}. Data missing")
            warnings.warn(
                VisualizationSetupWarning(f"Cannot plot {metric}. Data missing")
            )
            continue
        mode = "lines"
        y_converter: Callable[[pd.Series], pd.Series] = lambda s: s.fillna(0).astype(
            int
        )
        if metric == PlotMetric.CADENCE:
            mode = "markers"
        elif metric == PlotMetric.SPEED:
            y_converter = lambda s: s * 3.6

        y_data = y_converter(data_for_plot[metric])

        if add_zones and metric in METRICS_WITH_ZONES:
            fill = None
            if metric in [PlotMetric.HEARTRATE, PlotMetric.POWER]:
                fill = "tozeroy"

            _add_scatter_disonct(
                fig=fig,
                data=data_for_plot,
                metric=metric,
                mode=mode,
                fill=fill,
                y_converter=y_converter,
                y_range_max_factor=1.2,
                y_range_min_factor=0.6,
                title=f"{metric.capitalize()} [{ENRICH_UNITS[metric]}]",
                is_secondary=secondary,
            )
        else:
            y_max = max(y_max, y_data.max() * 1.2)
            dmin = y_data.min()
            y_min = min(y_min, dmin * 0.6 if dmin > 0 else dmin * 1.5)
            _add_scatter_cont(
                fig=fig,
                x=x_data,
                y=y_data,
                mode=mode,
                color=color,
                title=f"{metric.capitalize()} [{ENRICH_UNITS[metric]}]",
                y_range=None,
                is_secondary=secondary,
                show_legend=len(metrics) > 2,
            )
    if slider:
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
            )
        )

    if base == PlotBase.DISTANCE:
        fig.update_xaxes(title_text="Distance [m]")
    else:
        fig.update_layout(
            xaxis=dict(
                title="Duration [HH:MM:SS]",
                tickformat="%H:%M:%S",
            )
        )
    if height is not None:
        fig.update_layout(height=height)
    if width is not None:
        fig.update_layout(width=width)

    if len(metrics) == 1:
        metric = metrics[0]
        fig.update_yaxes(title_text=f"{metric.capitalize()} [{ENRICH_UNITS[metric]}]")
    elif len(metrics) > 2:
        fig.update_yaxes(title_text=None)
        fig.update_yaxes(range=(y_min, y_max), secondary_y=add_zones)
    return fig

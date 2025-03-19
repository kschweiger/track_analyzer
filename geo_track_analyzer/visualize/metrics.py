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

from .constants import ENRICH_UNITS


class PlotMetric(StrEnum):
    ELEVATION = auto()
    HEARTRATE = auto()
    POWER = auto()
    CADENCE = auto()
    SPEED = auto()


class PlotBase(StrEnum):
    DISTANCE = "cum_distance_moving"
    DURATION = "cum_time_moving"


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
) -> Figure:
    assert len(metrics) == len(set(metrics))

    if colors is None:
        _colors = [None for _ in metrics]
    else:
        if len(metrics) < len(colors):
            raise VisualizationSetupError(
                "Colors have been passed but at least "
                "the same number as metrics is required"
            )
        _colors = colors

    set_secondary = [False, True] if len(metrics) == 2 else [False for _ in metrics]

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

        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=y_data,
                mode=mode,
                name=f"{metric.capitalize()} [{ENRICH_UNITS[metric]}]",
                marker_color=color,
            ),
            secondary_y=secondary,
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
    return fig

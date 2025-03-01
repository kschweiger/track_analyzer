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


class ProgressionMetric(StrEnum):
    ELEVATION = auto()
    HEARTRATE = auto()
    POWER = auto()
    CADENCE = auto()
    SPEED = auto()


class ProgressionBase(StrEnum):
    DISTANCE = "cum_distance_moving"
    DURATION = "cum_time_moving"


def plot_progressions(
    data: pd.DataFrame,
    *,
    metrics: Annotated[list[ProgressionMetric], "Unique values"],
    base: ProgressionBase = ProgressionBase.DISTANCE,
    strict_data_selection: bool = False,
) -> Figure:
    assert len(metrics) == len(set(metrics))

    set_secondary = [False, True] if len(metrics) == 2 else [False for _ in metrics]

    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot: pd.DataFrame = data[mask].copy()  # type: ignore

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if base == ProgressionBase.DISTANCE:
        x_data = data_for_plot[base]
    else:
        x_data = pd.to_timedelta(data_for_plot[base], unit="s") + pd.Timestamp(
            "1970/01/01"
        )

    for metric, secondary in zip(metrics, set_secondary):
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
        if metric == ProgressionMetric.CADENCE:
            mode = "markers"
        elif metric == ProgressionMetric.SPEED:
            y_converter = lambda s: s * 3.6

        y_data = y_converter(data_for_plot[metric])

        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=y_data,
                mode=mode,
                name=f"{metric.capitalize()} [{ENRICH_UNITS[metric]}]",
            ),
            secondary_y=secondary,
        )

    if base == ProgressionBase.DISTANCE:
        fig.update_xaxes(title_text="Distance [m]")
    else:
        fig.update_layout(
            xaxis=dict(
                title="Duration [HH:MM:SS]",
                tickformat="%H:%M:%S",
            )
        )
    return fig

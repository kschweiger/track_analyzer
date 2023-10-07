import logging

import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure

logger = logging.getLogger(__name__)


def plot_track_3d(data: pd.DataFrame, strict_data_selection: bool = False) -> Figure:
    mask = data.moving
    if strict_data_selection:
        mask = mask & data.in_speed_percentile

    data_for_plot = data[mask]

    return px.line_3d(data_for_plot, x="latitude", y="longitude", z="elevation")

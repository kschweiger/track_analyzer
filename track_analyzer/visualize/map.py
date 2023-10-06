import logging

import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure

from track_analyzer.utils import center_geolocation

logger = logging.getLogger(__name__)


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

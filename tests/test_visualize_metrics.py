import random
from datetime import datetime, timedelta

import numpy as np
import pytest
from plotly.graph_objs import Figure

from geo_track_analyzer.model import ZoneInterval, Zones
from geo_track_analyzer.track import PyTrack, Track
from geo_track_analyzer.visualize.metrics import PlotBase, PlotMetric


@pytest.fixture
def full_track() -> Track:
    km_per_degree_at_equator = 111.32  # Approximate km per degree at the equator
    speed = 20  # km/h
    distance_per_step = 0.1 * km_per_degree_at_equator  # km
    time_per_step = distance_per_step / speed  # hours
    points = [
        (lat, long) for lat, long in zip(np.zeros(100), np.arange(0, 10, 0.1)[:100])
    ]
    times = np.arange(0, 100) * time_per_step
    datetime_list = [datetime.today() + timedelta(hours=hours) for hours in times]

    return PyTrack(
        points=points,
        elevations=[200 + random.randrange(20) for _ in range(100)],
        times=datetime_list,
        heartrate=[80] * 20 + [100] * 30 + [140] * 30 + [90] * 20,
        cadence=[70] * 30 + [80] * 30 + [70] * 40,
        power=[200] * 50 + [400] * 50,
        heartrate_zones=Zones(
            intervals=[
                ZoneInterval(start=None, end=85, color="#FF0000"),
                ZoneInterval(start=85, end=120, color="#00FF00"),
                ZoneInterval(start=120, end=None, color="#0000FF"),
            ]
        ),
        cadence_zones=Zones(
            intervals=[
                ZoneInterval(start=None, end=75, color="#FF0000"),
                ZoneInterval(start=75, end=85, color="#00FF00"),
                ZoneInterval(start=85, end=None, color="#0000FF"),
            ]
        ),
        power_zones=Zones(
            intervals=[
                ZoneInterval(start=None, end=250, color="#FF0000"),
                ZoneInterval(start=250, end=None, color="#0000FF"),
            ]
        ),
    )


@pytest.mark.parametrize("metric", [m for m in PlotMetric])
@pytest.mark.parametrize("base", [b for b in PlotBase])
@pytest.mark.parametrize("color", [None, ["#FF00FF"]])
@pytest.mark.parametrize("slider", [True, False])
def test_plot_single_metrics(
    full_track: Track,
    base: str,
    metric: str,
    color: list[str] | None,
    slider: bool,
) -> None:
    fig = full_track.plot(
        kind="metrics",
        metrics=[metric],
        base=base,
        colors=color,
        slider=slider,
        height=300,
        width=900,
    )
    # fig.show()

    assert isinstance(fig, Figure)

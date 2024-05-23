from datetime import timedelta
from typing import Literal

import numpy as np
import pandas as pd
import pytest
from gpxpy.gpx import GPXTrack

from geo_track_analyzer.model import Position2D, ZoneInterval, Zones
from geo_track_analyzer.processing import (
    _recalc_cumulated_columns,
    add_zones_to_dataframe,
    get_processed_segment_data,
    get_processed_track_data,
    split_data,
    split_data_by_time,
)
from geo_track_analyzer.track import Track
from geo_track_analyzer.utils.base import distance


def test_get_processed_track_data(track_for_test: Track) -> None:
    (
        track_time,
        track_distance,
        track_stopped_time,
        track_stopped_distance,
        track_data,
    ) = get_processed_track_data(track_for_test.track)

    assert isinstance(track_time, float)
    assert isinstance(track_distance, float)
    assert isinstance(track_stopped_time, float)
    assert isinstance(track_stopped_distance, float)

    assert (
        track_data.cum_distance_moving.iloc[-1]
        == track_data[track_data.moving].distance.sum()
    )


def test_recalc_cumulated_columns() -> None:
    data = pd.DataFrame(
        {
            "distance": [10, 10, 10, 10, 20, 20, 20, 20],
            "time": [5, 5, 5, 5, 6, 6, 6, 6],
            "cum_time": [5, 10, 15, 20, 6, 12, 18, 24],
            "cum_time_moving": [0, 5, 10, 15, 6, 12, 18, 18],
            "cum_distance": [10, 20, 30, 40, 20, 40, 60, 80],
            "cum_distance_moving": [0, 10, 20, 30, 20, 40, 60, 60],
            "cum_distance_stopped": [10, 10, 10, 10, 10, 10, 10, 30],
            "moving": [False, True, True, True, True, True, True, False],
        }
    )

    ret_data = _recalc_cumulated_columns(data)

    assert ret_data.cum_time.iloc[-1] == ret_data.time.sum()
    assert ret_data.cum_distance.iloc[-1] == ret_data.distance.sum()

    assert (
        ret_data.cum_distance_moving.iloc[-1]
        == ret_data[ret_data.moving].distance.sum()
    )

    assert (
        ret_data.cum_distance_stopped.iloc[-1]
        == ret_data[~ret_data.moving].distance.sum()
    )

    assert ret_data.cum_time_moving.iloc[-1] == ret_data[ret_data.moving].time.sum()


# NOTE: expected value depends on track_for_test fixture. Keep in mind if fixture is
# NOTE: changed and this tests fails afterwards
@pytest.mark.parametrize("method", ["first", "closest"])
@pytest.mark.parametrize(
    ("split_by", "split_at", "moving_only"),
    [
        ("distance", 100, True),
        ("distance", 100, False),
        ("time", 100, True),
        ("time", 100, False),
    ],
)
def test_split_data(
    track_for_test: Track,
    split_by: Literal["distance", "time"],
    split_at: float,
    moving_only: bool,
    method: Literal["first", "closest", "interploation"],
) -> None:
    data = track_for_test.get_track_data()

    ret_data = split_data(
        data,
        split_at=split_at,
        split_by=split_by,
        moving_only=moving_only,
        method=method,
    )

    if moving_only:
        comp_col = (
            "cum_distance_moving" if split_by == "distance" else "cum_time_moving"
        )
    else:
        comp_col = "cum_distance" if split_by == "distance" else "cum_time"

    assert not ret_data.compare(data).empty

    assert (
        len(ret_data.segment.unique()) == (ret_data[comp_col].iloc[-1] // split_at) + 1
    )


def test_split_data_unity(track_for_test: Track) -> None:
    data = track_for_test.get_track_data()

    ret_data = split_data(data, split_by="distance", split_at=10_000)

    assert ret_data.compare(data).empty


def test_split_data_by_time(track_for_test: Track) -> None:
    data = track_for_test.get_track_data()

    ret_data = split_data_by_time(data, split_at=timedelta(seconds=100))

    assert not ret_data.compare(data).empty


def check_forward_points_in_segment(data: pd.DataFrame, track: GPXTrack) -> None:
    return (
        (
            data[data.segment == 0].iloc[-1].latitude
            == track.segments[1].points[0].latitude
        )
        and (
            data[data.segment == 0].iloc[-1].longitude
            == track.segments[1].points[0].longitude
        )
        and (
            data[data.segment == 1].iloc[-1].latitude
            == track.segments[2].points[0].latitude
        )
        and (
            data[data.segment == 1].iloc[-1].longitude
            == track.segments[2].points[0].longitude
        )
    )


def check_backward_points_in_segment(data: pd.DataFrame, track: GPXTrack) -> None:
    return (
        (
            data[data.segment == 1].iloc[0].latitude
            == track.segments[1].points[0].latitude
        )
        and (
            data[data.segment == 1].iloc[0].longitude
            == track.segments[1].points[0].longitude
        )
        and (
            data[data.segment == 2].iloc[0].latitude
            == track.segments[2].points[0].latitude
        )
        and (
            data[data.segment == 2].iloc[0].longitude
            == track.segments[2].points[0].longitude
        )
    )


def test_get_processed_track_data_connect_segments_forward(
    track_for_test_3_segments: Track,
) -> None:
    no_connection_datas = []
    for segment in track_for_test_3_segments.track.segments:
        _, _, _, _, _data_no_connect = get_processed_segment_data(segment=segment)
        no_connection_datas.append(_data_no_connect)

    data_no_connect = pd.concat(no_connection_datas).reset_index(drop=True)

    _, _, _, _, data_connect = get_processed_track_data(
        track_for_test_3_segments.track, connect_segments="forward"
    )

    assert len(data_no_connect) + 2 == len(data_connect)

    assert check_forward_points_in_segment(
        data_connect, track_for_test_3_segments.track
    )
    assert not check_backward_points_in_segment(
        data_connect, track_for_test_3_segments.track
    )


def test_get_processed_track_data_connect_segments_full(
    track_for_test_3_segments: Track,
) -> None:
    no_connection_datas = []
    for segment in track_for_test_3_segments.track.segments:
        _, _, _, _, _data_no_connect = get_processed_segment_data(segment=segment)
        no_connection_datas.append(_data_no_connect)

    data_no_connect = pd.concat(no_connection_datas).reset_index(drop=True)

    _, _, _, _, data_connect = get_processed_track_data(
        track_for_test_3_segments.track, connect_segments="full"
    )

    assert len(data_no_connect) + 4 == len(data_connect)

    assert check_forward_points_in_segment(
        data_connect, track_for_test_3_segments.track
    )
    assert check_backward_points_in_segment(
        data_connect, track_for_test_3_segments.track
    )


def test_compare_pp_distance_to_processed_track(track_for_test: Track) -> None:
    data = track_for_test.get_track_data()

    points = []
    for seg in track_for_test.track.segments:
        points.extend(seg.points)

    distances_for_sum = [0.0]
    for i in range(len(points) - 1):
        distances_for_sum.append(
            distance(
                Position2D(latitude=points[i].latitude, longitude=points[i].longitude),
                Position2D(
                    latitude=points[i + 1].latitude, longitude=points[i + 1].longitude
                ),
            )
        )

    cum_distance = np.cumsum(distances_for_sum)

    assert 0.99 < cum_distance[-1] / data.cum_distance.iloc[-1] < 1.01


def test_add_zones_to_dataframe() -> None:
    data = pd.DataFrame({"heartrate": [100, 100, 120, None, 100, 140, 200, None, None]})
    zones = Zones(
        intervals=[
            ZoneInterval(start=None, end=110),
            ZoneInterval(start=110, end=130),
            ZoneInterval(start=130, end=150),
            ZoneInterval(start=150, end=None),
        ]
    )

    data = add_zones_to_dataframe(data, "heartrate", zones)

    assert "heartrate_zones" in data.keys()
    assert data["heartrate_zones"].equals(
        pd.Series(
            [
                "Zone 1 [0, 110]",
                "Zone 1 [0, 110]",
                "Zone 2 [110, 130]",
                "Zone 1 [0, 110]",
                "Zone 1 [0, 110]",
                "Zone 3 [130, 150]",
                "Zone 4 [150, \u221e]",
                "Zone 1 [0, 110]",
                "Zone 1 [0, 110]",
            ]
        )
    )

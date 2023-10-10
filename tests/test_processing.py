from datetime import timedelta
from typing import Literal

import pandas as pd
import pytest

from track_analyzer.processing import (
    _recalc_cumulated_columns,
    get_processed_track_data,
    split_data,
    split_data_by_time,
)
from track_analyzer.track import Track


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

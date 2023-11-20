import logging
from datetime import timedelta
from typing import Any, Callable, Dict, Literal, Union

import numpy as np
import pandas as pd
from gpxpy.gpx import GPXTrack, GPXTrackSegment

from track_analyzer.exceptions import GPXPointExtensionError
from track_analyzer.utils.base import get_extension_value

logger = logging.getLogger(__name__)


def _recalc_cumulated_columns(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data.cum_time = data.time.cumsum()
    data.cum_distance = data.distance.cumsum()

    cum_time_moving: list[None] | list[float] = []
    cum_distance_moving = []
    cum_distance_stopped = []
    for idx, rcrd in enumerate(data.to_dict("records")):
        if idx == 0:
            if rcrd["time"] is None:
                cum_time_moving.append(None)  # type: ignore
            else:
                cum_time_moving.append(rcrd["time"] if rcrd["moving"] else 0)

            cum_distance_moving.append(rcrd["distance"] if rcrd["moving"] else 0)
            cum_distance_stopped.append(0 if rcrd["moving"] else rcrd["distance"])
        else:
            if rcrd["time"] is None:
                cum_time_moving.append(None)  # type: ignore
            else:
                cum_time_moving.append(
                    cum_time_moving[-1] + (rcrd["time"] if rcrd["moving"] else 0)
                )

            cum_distance_moving.append(
                cum_distance_moving[-1] + (rcrd["distance"] if rcrd["moving"] else 0)
            )
            cum_distance_stopped.append(
                cum_distance_stopped[-1] + (0 if rcrd["moving"] else rcrd["distance"])
            )

    data.cum_time_moving = cum_time_moving
    data.cum_distance_moving = cum_distance_moving
    data.cum_distance_stopped = cum_distance_stopped

    return data


def get_processed_track_data(
    track: GPXTrack,
    stopped_speed_threshold: float = 1,
) -> tuple[float, float, float, float, pd.DataFrame]:
    track_time: float = 0
    track_distance: float = 0
    track_stopped_time: float = 0
    track_stopped_distance: float = 0
    track_data: None | pd.DataFrame = None

    for i_segment, segment in enumerate(track.segments):
        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            _data,
        ) = get_processed_segment_data(segment, stopped_speed_threshold)

        track_time += time
        track_distance += distance
        track_stopped_time += stopped_time
        track_stopped_distance += stopped_distance

        data = _data.copy()
        data["segment"] = i_segment

        if track_data is None:
            track_data = data
        else:
            track_data = pd.concat([track_data, data]).reset_index(drop=True)

    # Not really possible but keeps linters happy
    if track_data is None:
        raise RuntimeError("Track has no segments")

    # Recalculate all cumulated columns over the segments
    track_data = _recalc_cumulated_columns(track_data)

    return (
        track_time,
        track_distance,
        track_stopped_time,
        track_stopped_distance,
        track_data,
    )


def get_processed_segment_data(
    segment: GPXTrackSegment, stopped_speed_threshold: float = 1
) -> tuple[float, float, float, float, pd.DataFrame]:
    """
    Calculate the speed and distance from point to point for a segment. This follows
    the implementation of the get_moving_data method in the implementation of
    gpx.GPXTrackSegment

    Args:
        segment: GPXTrackSegment to process
        stopped_speed_threshold: Threshold in km/h for speeds counting as moving.
                                 Default is 1 km/h

    Returns:

    """

    threshold_ms = stopped_speed_threshold / 3.6

    data: Dict[str, list[None | Union[float, bool]]] = {
        "latitude": [],
        "longitude": [],
        "elevation": [],
        "speed": [],
        "distance": [],
        "heartrate": [],
        "cadence": [],
        "power": [],
        "time": [],
        "cum_time": [],
        "cum_time_moving": [],
        "cum_distance": [],
        "cum_distance_moving": [],
        "cum_distance_stopped": [],
        "moving": [],
    }

    if segment.has_times():
        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            data,
        ) = get_processed_data_w_time(segment, data, threshold_ms)
    else:
        distance, data = get_processed_data_wo_time(segment, data)
        time, stopped_distance, stopped_time = 0, 0, 0

    data_df = pd.DataFrame(data)

    return (time, distance, stopped_time, stopped_distance, data_df)


def get_processed_data_w_time(
    segment: GPXTrackSegment, data: Dict[str, list[Any]], threshold_ms: float
) -> tuple[float, float, float, float, Dict[str, list[Any]]]:
    time = 0.0
    stopped_time = 0.0

    distance = 0.0
    stopped_distance = 0.0

    cum_time = 0
    cum_time_moving = 0

    cum_distance = 0
    cum_moving = 0
    cum_stopped = 0
    for previous, point in zip(segment.points, segment.points[1:]):
        # Ignore first and last point
        if point.time and previous.time:
            timedelta = point.time - previous.time

            if point.elevation and previous.elevation:
                point_distance = point.distance_3d(previous)
            else:
                point_distance = point.distance_2d(previous)

            seconds = timedelta.total_seconds()
            if seconds > 0 and point_distance is not None:
                if point_distance:
                    is_stopped = (
                        True if (point_distance / seconds) <= threshold_ms else False
                    )

                    data["distance"].append(point_distance)

                    if is_stopped:
                        stopped_time += seconds
                        stopped_distance += point_distance
                        cum_stopped += point_distance
                        data["moving"].append(False)
                    else:
                        time += seconds
                        distance += point_distance
                        cum_moving += point_distance
                        data["moving"].append(True)

                    cum_distance += point_distance
                    cum_time += seconds
                    data["time"].append(seconds)
                    data["cum_time"].append(cum_time)

                    data["cum_distance"].append(cum_distance)
                    data["cum_distance_moving"].append(cum_moving)
                    data["cum_distance_stopped"].append(cum_stopped)

                    data["latitude"].append(point.latitude)
                    data["longitude"].append(point.longitude)
                    if point.has_elevation():
                        data["elevation"].append(point.elevation)
                    else:
                        data["elevation"].append(None)

                    if not is_stopped:
                        data["speed"].append(point_distance / seconds)
                        cum_time_moving += seconds
                        data["cum_time_moving"].append(cum_time_moving)
                    else:
                        data["speed"].append(None)
                        data["cum_time_moving"].append(None)

                    for key in ["heartrate", "cadence", "power"]:
                        try:
                            data[key].append(float(get_extension_value(point, key)))
                        except GPXPointExtensionError:
                            data[key].append(None)

    return time, distance, stopped_time, stopped_distance, data


def get_processed_data_wo_time(
    segment: GPXTrackSegment, data: Dict[str, list[Any]]
) -> tuple[float, Dict[str, list[Any]]]:
    cum_distance = 0
    distance = 0.0
    for previous, point in zip(segment.points, segment.points[1:]):
        if point.elevation and previous.elevation:
            point_distance = point.distance_3d(previous)
        else:
            point_distance = point.distance_2d(previous)
        if point_distance is not None:
            distance += point_distance

            data["distance"].append(point_distance)
            data["latitude"].append(point.latitude)
            data["longitude"].append(point.longitude)
            if point.has_elevation():
                data["elevation"].append(point.elevation)
            else:
                data["elevation"].append(None)

            cum_distance += point_distance
            data["time"].append(None)
            data["cum_time"].append(None)
            data["cum_time_moving"].append(None)
            data["cum_distance"].append(cum_distance)
            data["cum_distance_moving"].append(cum_distance)
            data["cum_distance_stopped"].append(None)
            data["speed"].append(None)
            data["moving"].append(True)

            for key in ["heartrate", "cadence", "power"]:
                try:
                    data[key].append(float(get_extension_value(point, key)))
                except GPXPointExtensionError:
                    data[key].append(None)

    return distance, data


def split_data_by_time(
    data: pd.DataFrame,
    split_at: timedelta,
    moving_only: bool = True,
    method: Literal["first", "closest", "interploation"] = "closest",
) -> pd.DataFrame:
    return split_data(
        data=data,
        split_by="time",
        split_at=split_at.total_seconds(),
        moving_only=moving_only,
        method=method,
    )


def split_data(
    data: pd.DataFrame,
    split_by: Literal["distance", "time"],
    split_at: float,
    moving_only: bool = True,
    method: Literal["first", "closest", "interploation"] = "closest",
) -> pd.DataFrame:
    split_idx_finder: Callable[[pd.Series, float], int]
    if method == "closest":
        split_idx_finder = lambda s, v: np.abs(s.to_numpy() - v).argmin()
    # TODO: Implement method in which the plotting point is interpolat to the ecxat val
    elif method == "interploation":
        raise NotImplementedError("Interploation splitting method not implemented")
    else:
        split_idx_finder = lambda s, v: s[s < v].index.max()

    data = data.copy()

    if split_by == "distance":
        column = "cum_distance_moving" if moving_only else "cum_distance"
    else:
        column = "cum_time_moving" if moving_only else "cum_time"

    max_value = data[column].max()

    if split_at > max_value:
        logger.warning(
            "Data can not be split further by %s with passed value %s",
            split_by,
            split_at,
        )
        return data

    split_vals = [split_at]
    while split_vals[-1] < max_value:
        split_vals.append(split_vals[-1] + split_at)

    split_vals = split_vals[:-1]

    logger.debug("Splitting into %s segments", len(split_vals))

    last_split = 0
    i_segement = 0
    for val in split_vals:
        split_idx = split_idx_finder(data[column], val)
        data.loc[last_split:split_idx, "segment"] = i_segement
        last_split = split_idx + 1
        i_segement += 1

    if last_split != data.index.max() + 1:
        data.loc[last_split : data.index.max() + 1, "segment"] = i_segement

    return data

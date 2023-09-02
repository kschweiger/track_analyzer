from typing import Any, Dict, Union

import pandas as pd
from gpxpy.gpx import GPXTrackSegment


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
                    data["cum_distance"].append(cum_distance)
                    data["cum_distance_moving"].append(cum_moving)
                    data["cum_distance_stopped"].append(cum_stopped)

                    if not is_stopped:
                        data["speed"].append(point_distance / seconds)
                        data["latitude"].append(point.latitude)
                        data["longitude"].append(point.longitude)
                        if point.has_elevation():
                            data["elevation"].append(point.elevation)
                        else:
                            data["elevation"].append(None)
                    else:
                        data["speed"].append(None)
                        data["latitude"].append(None)
                        data["longitude"].append(None)
                        data["elevation"].append(None)
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
            data["cum_distance"].append(cum_distance)
            data["cum_distance_moving"].append(cum_distance)
            data["cum_distance_stopped"].append(None)
            data["speed"].append(None)
            data["moving"].append(True)

    return distance, data

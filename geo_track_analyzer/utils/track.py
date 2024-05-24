from itertools import pairwise
from typing import Literal

import pandas as pd

from geo_track_analyzer.exceptions import VisualizationSetupError
from geo_track_analyzer.processing import (
    get_processed_segment_data,
    get_processed_track_data,
)
from geo_track_analyzer.track import Track, logger


def extract_track_data_for_plot(
    track: Track,
    kind: str,
    require_elevation: list[str],
    intervals: None | int = None,
    connect_segments: Literal["full", "forward"] = "forward",
) -> pd.DataFrame:
    """Extract the data from a Track as DataFrame for plotting.

    :param track: Track object
    :param kind: Kind of plot
    :param require_elevation: List of kinds of plots that require elevation data to be
        present in the Track
    :param intervals: Optionally reduce the pp-distance in the track, defaults to None

    :return: DataFrame
    """
    if kind in require_elevation and not track.track.has_elevations():
        raise VisualizationSetupError(f"Track has so elevation so {kind} is not valid")
    _track = track.track

    if intervals is not None:
        if track.get_avg_pp_distance() >= intervals:
            logger.debug("Average pp distance larget than interval. Skipping reduction")
        else:
            _track = _track.clone()
            _track.reduce_points(intervals)

    _, _, _, _, data = get_processed_track_data(
        _track,
        connect_segments=connect_segments,
        heartrate_zones=track.heartrate_zones,
        power_zones=track.power_zones,
        cadence_zones=track.cadence_zones,
    )

    return data


def extract_multiple_segment_data_for_plot(
    track: Track,
    segments: list[int],
    kind: str,
    require_elevation: list[str],
    intervals: None | int = None,
    connect_segments: Literal["full", "forward"] = "forward",
) -> pd.DataFrame:
    """Extract the data for a two or more segments from a Track as DataFrame for
    plotting.

    :param track: Track object
    :param segments: Indices of the segments to be extracted
    :param kind: Kind of plot
    :param require_elevation: List of kinds of plots that require elevation data to be
        present in the Track
    :param intervals: Optionally reduce the pp-distance in the track, defaults to None

    :return: DataFrame
    """
    if len(segments) < 2:
        raise VisualizationSetupError("Pass at least two segment ids")
    if max(segments) >= track.n_segments or min(segments) < 0:
        raise VisualizationSetupError(
            f"Passed ids must be between 0 and {len(segments)-1}. Got {segments}"
        )

    data = extract_track_data_for_plot(
        track=track,
        kind=kind,
        require_elevation=require_elevation,
        intervals=intervals,
        connect_segments=connect_segments,
    )

    return data[data.segment.isin(segments)]


def extract_segment_data_for_plot(
    track: Track,
    segment: int,
    kind: str,
    require_elevation: list[str],
    intervals: None | int = None,
) -> pd.DataFrame:
    """Extract the data for a segment from a Track as DataFrame for plotting.

    :param track: Track object
    :param segment: Index of the segment to be extracted
    :param kind: Kind of plot
    :param require_elevation: List of kinds of plots that require elevation data to be
        present in the Track
    :param intervals: Optionally reduce the pp-distance in the track, defaults to None

    :return: DataFrame
    """
    if kind in require_elevation and not track.track.segments[segment].has_elevations():
        raise VisualizationSetupError(
            f"Segment has so elevation so {kind} is not valid"
        )
    if kind == "map-segments":
        raise VisualizationSetupError("map-segments can only be done for full tracks")

    segement = track.track.segments[segment]

    if intervals is not None:
        if track.get_avg_pp_distance_in_segment(segment) >= intervals:
            logger.debug("Average pp distance larget than interval. Skipping reduction")
        else:
            segement = track.track.segments[segment].clone()
            segement.reduce_points(intervals)

    _, _, _, _, data = get_processed_segment_data(
        segement,
        heartrate_zones=track.heartrate_zones,
        power_zones=track.power_zones,
        cadence_zones=track.cadence_zones,
    )

    return data


def generate_distance_segments(data: pd.DataFrame, distance: float) -> pd.DataFrame:
    """Generate segments with the distance specified with the passed parameter. Segments
    present in the passed data will be replaced. Splitting is done based on the
    distance_moving value in the data. Segements are split closest to the passed
    distance. So extact cummulated distance in a segment depends on the pp-distance in
    the track. The last segmeent may be shorter than the passed distance.

    :param data: Dataframe create with extract_track_data_for_plot,
        extract_segment_data_for_plot, or extract_multiple_segment_data_for_plot
        methods.
    :param distance: Intended segmeent distance

    :return: Dataframe with updated segments
    """
    key = "cum_distance_moving"
    max_distance = data.iloc[-1][key]

    if max_distance < distance:
        data["segment"] = 0
        return data

    distances, segments_ids = [0.0], [0]
    while distances[-1] < max_distance:
        distances.append(distances[-1] + distance)
        segments_ids.append(segments_ids[-1] + 1)

    new_segments = data.segment.copy()
    new_segments.loc[:] = max(segments_ids)
    for (start, end), idx in zip(pairwise(distances), segments_ids):
        new_segments.iloc[data[(data[key] >= start) & (data[key] < end)].index] = idx

    data["segment"] = new_segments
    return data

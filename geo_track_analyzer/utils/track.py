from typing import Literal

import pandas as pd

from geo_track_analyzer.exceptions import VisualizationSetupError
from geo_track_analyzer.model import Zones
from geo_track_analyzer.processing import (
    add_zones_to_dataframe,
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
    heartrate_zones: None | Zones = None,
    power_zones: None | Zones = None,
    cadence_zones: None | Zones = None,
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
        _track, connect_segments=connect_segments
    )

    if heartrate_zones is not None:
        data = add_zones_to_dataframe(data, "heartrate", heartrate_zones)
    if power_zones is not None:
        data = add_zones_to_dataframe(data, "power", power_zones)
    if cadence_zones is not None:
        data = add_zones_to_dataframe(data, "cadence", cadence_zones)

    return data


def extract_multiple_segment_data_for_plot(
    track: Track,
    segments: list[int],
    kind: str,
    require_elevation: list[str],
    intervals: None | int = None,
    connect_segments: Literal["full", "forward"] = "forward",
    heartrate_zones: None | Zones = None,
    power_zones: None | Zones = None,
    cadence_zones: None | Zones = None,
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
        heartrate_zones=heartrate_zones,
        power_zones=power_zones,
        cadence_zones=cadence_zones,
    )

    return data[data.segment.isin(segments)]


def extract_segment_data_for_plot(
    track: Track,
    segment: int,
    kind: str,
    require_elevation: list[str],
    intervals: None | int = None,
    heartrate_zones: None | Zones = None,
    power_zones: None | Zones = None,
    cadence_zones: None | Zones = None,
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

    _, _, _, _, data = get_processed_segment_data(segement)

    if heartrate_zones is not None:
        data = add_zones_to_dataframe(data, "heartrate", heartrate_zones)
    if power_zones is not None:
        data = add_zones_to_dataframe(data, "heartrate", power_zones)
    if cadence_zones is not None:
        data = add_zones_to_dataframe(data, "heartrate", cadence_zones)

    return data

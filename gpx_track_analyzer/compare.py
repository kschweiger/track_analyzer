import logging
from collections import deque
from functools import lru_cache
from typing import Tuple

import numpy as np
from gpxpy.gpx import GPXTrackSegment

from gpx_track_analyzer.model import Position2D, SegmentOverlap
from gpx_track_analyzer.utils import (
    crop_segment_to_bounds,
    distance,
    get_latitude_at_distance,
    get_longitude_at_distance,
    get_point_distance_in_segment,
)

logger = logging.getLogger(__name__)


def check_segment_bound_overlap(
    reference_segments: GPXTrackSegment, segments: list[GPXTrackSegment]
) -> list[bool]:
    reference_bounds = reference_segments.get_bounds()

    res = []

    for segment in segments:
        bounds = segment.get_bounds()

        res.append(
            bounds.min_latitude < reference_bounds.max_latitude
            and bounds.min_longitude < reference_bounds.max_latitude
            and bounds.max_latitude > reference_bounds.min_latitude
            and bounds.max_longitude > reference_bounds.min_longitude
        )

    return res


@lru_cache(100)
def derive_plate_bins(
    gird_width: float,
    bounds_min_latitude: float,
    bounds_min_longitude: float,
    bounds_max_latitude: float,
    bounds_max_longitude: float,
) -> Tuple[list[Tuple[float, float]], list[Tuple[float, float]]]:
    """
    Derive the lat/long bins based on the min/max lat/long values and the target
    bin width.

    :param gird_width:  Lengths (in m) each bin will have in latitude and longitude
                        direction
    :param bounds_min_longitude: Minimum longitude of the grid
    :param bounds_max_latitude: Maximum latitude of the gtid. Bins may end with larger
                                values than passed here dependeing on the grid width
    :param bounds_max_longitude: Maximum longitude of the grid. Bins may end with
                                 larger values than passed here dependeing on the
                                 grid width
    :return: Tuple with lists let/long values for the bin is latitude and longitude
             direction.
    """
    # Find the total distance in latitude and longitude directrons to find the number of
    # bins that need be generated bas ed on the pass gridwidth
    distance_latitude_total = gird_width + distance(
        Position2D(bounds_min_latitude, bounds_min_longitude),
        Position2D(bounds_max_latitude, bounds_min_longitude),
    )
    distance_longitude_total = gird_width + distance(
        Position2D(bounds_min_latitude, bounds_min_longitude),
        Position2D(bounds_min_latitude, bounds_max_longitude),
    )

    n_bins_latitude = int(round(distance_latitude_total / gird_width))
    n_bins_longitude = int(round(distance_longitude_total / gird_width))

    # The point at the lower bounds should be in the middle of the first bin. So
    # the edge of these bends need to be half the grid width from the original
    # lower left bound
    lower_edge_latitude = get_latitude_at_distance(
        Position2D(bounds_min_latitude, bounds_min_longitude), gird_width / 2, False
    )
    lower_edge_longitude = get_longitude_at_distance(
        Position2D(bounds_min_latitude, bounds_min_longitude), gird_width / 2, False
    )

    # Generate the bin edges by starting from the lower left edge and adding new
    # points with distance gid_width
    bins_latitude = [(lower_edge_latitude, lower_edge_longitude)]
    for _ in range(n_bins_latitude):
        bins_latitude.append(
            (
                get_latitude_at_distance(
                    Position2D(*bins_latitude[-1]), gird_width, True
                ),
                lower_edge_longitude,
            )
        )

    bins_longitude = [(lower_edge_latitude, lower_edge_longitude)]
    for _ in range(n_bins_longitude):
        bins_longitude.append(
            (
                lower_edge_latitude,
                get_longitude_at_distance(
                    Position2D(*bins_longitude[-1]), gird_width, True
                ),
            )
        )

    logger.debug(
        "Derived %s bins in latitude direction and %s in longitude direction",
        len(bins_latitude),
        len(bins_longitude),
    )
    logger.debug("  latitude direction: %s to %s", bins_latitude[0], bins_latitude[-1])
    logger.debug(
        "  longitude direction: %s to %s", bins_longitude[0], bins_longitude[-1]
    )

    return (bins_latitude, bins_longitude)


def convert_segment_to_plate(
    segment: GPXTrackSegment,
    gird_width: float,
    bounds_min_latitude: float,
    bounds_min_longitude: float,
    bounds_max_latitude: float,
    bounds_max_longitude: float,
    normalize: bool = False,
    max_queue_normalize: int = 5,
) -> np.ndarray:
    """
    Takes a GPXSegement and fills bins of a 2D array (called plate) with the passed
    bin width. Bins will start at the min latitude and longited values.

    :param segment: The GPXPoints of the Segment will be filled into the plate
    :param gird_width: Width (in meters) of the grid
    :param bounds_min_latitude: Minimum latitude of the grid
    :param bounds_min_longitude: Minimum longitude of the grid
    :param bounds_max_latitude: Maximum latitude of the gtid. Bins may end with larger
                                values than passed here dependeing on the grid width
    :param bounds_max_longitude: Maximum longitude of the grid. Bins may end with larger
                                values than passed here dependeing on the grid width
    :param normalize: If True, successive points (defined by the max_queue_normalize)
                      will not change the values in a bin. This means that each bin
                      values should have the value 1 except there is overlap with
                      points later in the track. To decide this the previous
                      max_queue_normalize points will be considered. So this value
                      dependes on the chosen gridwidth.
    :param max_queue_normalize: Number of previous bins considered when normalize is
                                set to true.
    :return: 2DArray representing the plate.
    """
    bins_latitude, bins_longitude = derive_plate_bins(
        gird_width,
        bounds_min_latitude,
        bounds_min_longitude,
        bounds_max_latitude,
        bounds_max_longitude,
    )

    _lat_bins = np.array([b[0] for b in bins_latitude])
    _long_bins = np.array([b[1] for b in bins_longitude])

    lats, longs = [], []
    for point in segment.points:
        lats.append(point.latitude)
        longs.append(point.longitude)

    # np.digitize starts with 1. We want 0 as first bin
    segment_lat_bins = np.digitize(lats, _lat_bins) - 1
    segment_long_bins = np.digitize(longs, _long_bins) - 1

    plate = np.zeros(shape=(len(bins_latitude), len(bins_longitude)))

    prev_bins = deque(maxlen=max_queue_normalize)  # type: ignore

    for lat, long in zip(segment_lat_bins, segment_long_bins):
        if normalize:
            if any((lat, long) == prev_bin for prev_bin in prev_bins):
                continue
            prev_bins.append((lat, long))
            plate[lat, long] += 1
        else:
            plate[lat, long] += 1

    return np.flip(plate, axis=0)


def get_segment_overlap(
    base_segment: GPXTrackSegment,
    match_segment: GPXTrackSegment,
    grid_width: float,
    max_queue_normalize: int = 5,
) -> SegmentOverlap:
    """Compare the tracks of two segements and caclulate the overlap.

    :param base_segment: Base segement in which the match segment should be found
    :param match_segment: Other segmeent that should be found in the base segement
    :param grid_width: Width (in meters) of the grid that will be filled to estimate
                       the overalp.
    :param max_queue_normalize: Minimum number of successive points in the segment
                                between to points falling into same plate bin.
    :return: Overlap plate (2D Array, 0 no overlap, 1 overlap), overlap value in [0, 1]
    """
    bounds_match = match_segment.get_bounds()

    cropped_base_segment = crop_segment_to_bounds(
        base_segment,
        bounds_match.min_latitude,
        bounds_match.min_longitude,
        bounds_match.max_latitude,
        bounds_match.max_longitude,
    )

    plate_base = convert_segment_to_plate(
        cropped_base_segment,
        grid_width,
        bounds_match.min_latitude,
        bounds_match.min_longitude,
        bounds_match.max_latitude,
        bounds_match.max_longitude,
        True,
        max_queue_normalize,
    )

    # Check if the match segment appears muzltiple times in the base segemnt
    if plate_base.max() > 1:
        logger.debug(
            "Multiple occurances of points within match bounds in base segment"
        )
        raise NotImplementedError("Multiple matches in base segement are not supported")
        # TODO: Split base_segement after first point exiting bounds and recursively
        # TODO: call this function as long as this block is entered.

    # TEMP
    # import plotly.express as px

    # fig = px.imshow(plate_base)
    # fig.show()
    # TEMP

    plate_match = convert_segment_to_plate(
        match_segment,
        grid_width,
        bounds_match.min_latitude,
        bounds_match.min_longitude,
        bounds_match.max_latitude,
        bounds_match.max_longitude,
        True,
        max_queue_normalize,
    )

    overlap_plate = plate_base + plate_match

    overlap_plate_ = np.digitize(overlap_plate, np.array([0, 2, 3])) - 1

    overlapping_bins = np.sum(overlap_plate_)
    match_bins = np.sum(plate_match)

    logger.debug(
        "%s overlapping bins and %s bins in match segment", overlapping_bins, match_bins
    )

    overlap = overlapping_bins / match_bins

    logger.debug("Overlap: %s", overlap)

    # Determine if the direction in the base segmeent matched the direction
    # in the match segement
    first_point_match, last_point_match = (
        match_segment.points[0],
        match_segment.points[-1],
    )

    # TODO: Decide if the first/last id's of the base segment per match should
    # TODO: be returned
    first_point_base, first_distance, first_idx = get_point_distance_in_segment(
        base_segment, first_point_match.latitude, first_point_match.longitude
    )

    last_point_base, last_distance, last_idx = get_point_distance_in_segment(
        base_segment, last_point_match.latitude, last_point_match.longitude
    )

    if last_idx > first_idx:
        logger.debug("Match direction: Same")
        inverse = False
        start_point, start_idx = first_point_base, first_idx
        end_point, end_idx = last_point_base, last_idx
    else:
        logger.debug("Match direction: Iverse")
        inverse = True
        end_point, end_idx = first_point_base, first_idx
        start_point, start_idx = last_point_base, last_idx

    return SegmentOverlap(
        overlap=overlap,
        inverse=inverse,
        plate=overlap_plate,
        start_point=start_point,
        start_idx=start_idx,
        end_point=end_point,
        end_idx=end_idx,
    )

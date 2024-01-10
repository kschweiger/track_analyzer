import logging
from collections import deque
from functools import lru_cache

import numpy as np
import numpy.typing as npt
from gpxpy.gpx import GPXTrack, GPXTrackSegment

from geo_track_analyzer.model import Position2D, SegmentOverlap
from geo_track_analyzer.utils.base import (
    check_bounds,
    crop_segment_to_bounds,
    distance,
    get_latitude_at_distance,
    get_longitude_at_distance,
    get_point_distance,
    get_points_inside_bounds,
    split_segment_by_id,
)

logger = logging.getLogger(__name__)


def check_segment_bound_overlap(
    reference_segments: GPXTrackSegment, segments: list[GPXTrackSegment]
) -> list[bool]:
    """Check if segments are within the bounds of a reference segment

    :param reference_segments: Segment defining the bounds inside which the other
        segments should be contained
    :param segments: Segments to be checked

    :return: List of bools specifying if the segments are inside the refence bounds
    """
    reference_bounds = reference_segments.get_bounds()

    check_bounds(reference_bounds)

    res = []

    for segment in segments:
        bounds = segment.get_bounds()

        check_bounds(bounds)

        res.append(
            bounds.min_latitude < reference_bounds.max_latitude  # type: ignore
            and bounds.min_longitude < reference_bounds.max_latitude  # type: ignore
            and bounds.max_latitude > reference_bounds.min_latitude  # type: ignore
            and bounds.max_longitude > reference_bounds.min_longitude  # type: ignore
        )

    return res


@lru_cache(100)
def derive_plate_bins(
    gird_width: float,
    bounds_min_latitude: float,
    bounds_min_longitude: float,
    bounds_max_latitude: float,
    bounds_max_longitude: float,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
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

    :return: tuple with lists let/long values for the bin is latitude and longitude
             direction.
    """
    # Find the total distance in latitude and longitude directrons to find the number of
    # bins that need be generated bas ed on the pass gridwidth
    distance_latitude_total = gird_width + distance(
        Position2D(latitude=bounds_min_latitude, longitude=bounds_min_longitude),
        Position2D(latitude=bounds_max_latitude, longitude=bounds_min_longitude),
    )
    distance_longitude_total = gird_width + distance(
        Position2D(latitude=bounds_min_latitude, longitude=bounds_min_longitude),
        Position2D(latitude=bounds_min_latitude, longitude=bounds_max_longitude),
    )

    n_bins_latitude = int(round(distance_latitude_total / gird_width))
    n_bins_longitude = int(round(distance_longitude_total / gird_width))

    # The point at the lower bounds should be in the middle of the first bin. So
    # the edge of these bends need to be half the grid width from the original
    # lower left bound
    lower_edge_latitude = get_latitude_at_distance(
        Position2D(latitude=bounds_min_latitude, longitude=bounds_min_longitude),
        gird_width / 2,
        False,
    )
    lower_edge_longitude = get_longitude_at_distance(
        Position2D(latitude=bounds_min_latitude, longitude=bounds_min_longitude),
        gird_width / 2,
        False,
    )

    # Generate the bin edges by starting from the lower left edge and adding new
    # points with distance gid_width
    bins_latitude = [(lower_edge_latitude, lower_edge_longitude)]
    for _ in range(n_bins_latitude):
        _this_lat, _this_lon = bins_latitude[-1]
        bins_latitude.append(
            (
                get_latitude_at_distance(
                    Position2D(latitude=_this_lat, longitude=_this_lon),
                    gird_width,
                    True,
                ),
                lower_edge_longitude,
            )
        )

    bins_longitude = [(lower_edge_latitude, lower_edge_longitude)]
    for _ in range(n_bins_longitude):
        _this_lat, _this_lon = bins_longitude[-1]
        bins_longitude.append(
            (
                lower_edge_latitude,
                get_longitude_at_distance(
                    Position2D(latitude=_this_lat, longitude=_this_lon),
                    gird_width,
                    True,
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


def _extract_ranges(
    base_points_in_bounds: list[tuple[int, bool]], allow_points_outside_bounds: int
) -> list[tuple[int, int]]:
    """Extract point ranges from a list of indices and boolan flags"""
    id_ranges_in_bounds: list[tuple[int, int]] = []
    found_range = False
    in_bound_range_start = -1
    points_since_last_range = 0
    idx = 0
    for idx, in_bounds in base_points_in_bounds:
        if in_bounds and not found_range:
            # Start of in_bound_points
            found_range = True
            if (
                points_since_last_range <= allow_points_outside_bounds
                and id_ranges_in_bounds
            ):
                prev_range_start, _ = id_ranges_in_bounds.pop()
                in_bound_range_start = prev_range_start
            else:
                in_bound_range_start = idx
        if not in_bounds:
            if found_range:
                # End of in_bound_points
                found_range = False
                id_ranges_in_bounds.append((in_bound_range_start, idx - 1))
                points_since_last_range = 0
            points_since_last_range += 1
    if found_range:
        id_ranges_in_bounds.append((in_bound_range_start, idx))

    return id_ranges_in_bounds


def get_segment_overlap(
    base_segment: GPXTrackSegment,
    match_segment: GPXTrackSegment,
    grid_width: float,
    max_queue_normalize: int = 5,
    allow_points_outside_bounds: int = 5,
    overlap_threshold: float = 0.75,
) -> list[SegmentOverlap]:
    """Compare the tracks of two segements and caclulate the overlap.

    :param base_segment: Base segement in which the match segment should be found
    :param match_segment: Other segmeent that should be found in the base segement
    :param grid_width: Width (in meters) of the grid that will be filled to estimate
                       the overalp.
    :param max_queue_normalize: Minimum number of successive points in the segment
                                between two points falling into same plate bin.
    :param allow_points_outside_bounds: Number of points between sub segments allowed
                                        for merging the segments.
    :param overlap_threshold: Minimum overlap required to return the overlap data.

    :return: list of SegmentOverlap objects.
    """
    bounds_match = match_segment.get_bounds()

    check_bounds(bounds_match)

    cropped_base_segment = crop_segment_to_bounds(
        base_segment,
        bounds_match.min_latitude,  # type: ignore
        bounds_match.min_longitude,  # type: ignore
        bounds_match.max_latitude,  # type: ignore
        bounds_match.max_longitude,  # type: ignore
    )

    plate_base = convert_segment_to_plate(
        cropped_base_segment,
        grid_width,
        bounds_match.min_latitude,  # type: ignore
        bounds_match.min_longitude,  # type: ignore
        bounds_match.max_latitude,  # type: ignore
        bounds_match.max_longitude,  # type: ignore
        True,
        max_queue_normalize,
    )

    plate_match = convert_segment_to_plate(
        match_segment,
        grid_width,
        bounds_match.min_latitude,  # type: ignore
        bounds_match.min_longitude,  # type: ignore
        bounds_match.max_latitude,  # type: ignore
        bounds_match.max_longitude,  # type: ignore
        True,
        max_queue_normalize,
    )

    # Check if the match segment appears muzltiple times in the base segemnt
    if plate_base.max() > 1:
        logger.debug(
            "Multiple occurances of points within match bounds in base segment"
        )
        base_points_in_bounds = get_points_inside_bounds(
            base_segment,
            bounds_match.min_latitude,  # type: ignore
            bounds_match.min_longitude,  # type: ignore
            bounds_match.max_latitude,  # type: ignore
            bounds_match.max_longitude,  # type: ignore
        )

        id_ranges_in_bounds = _extract_ranges(
            base_points_in_bounds, allow_points_outside_bounds
        )

        sub_segments = split_segment_by_id(base_segment, id_ranges_in_bounds)
        sub_segment_overlaps = []
        for i_sub_segment, (sub_segment, id_sub_segment) in enumerate(
            zip(sub_segments, id_ranges_in_bounds)
        ):
            logger.debug(
                "Processing overlap in sub-plate %s/%s",
                i_sub_segment + 1,
                len(sub_segments),
            )
            sub_plate = convert_segment_to_plate(
                sub_segment,
                grid_width,
                bounds_match.min_latitude,  # type: ignore
                bounds_match.min_longitude,  # type: ignore
                bounds_match.max_latitude,  # type: ignore
                bounds_match.max_longitude,  # type: ignore
                True,
                max_queue_normalize,
            )
            sub_segment_overlap = _calc_plate_overlap(
                base_segment=sub_segment,
                plate_base=sub_plate,
                match_segment=match_segment,
                plate_match=plate_match,
            )

            subseg_start, _ = id_sub_segment
            sub_segment_overlap.start_idx += subseg_start
            sub_segment_overlap.end_idx += subseg_start

            if sub_segment_overlap.overlap >= overlap_threshold:
                sub_segment_overlaps.append(sub_segment_overlap)

        return sorted(sub_segment_overlaps, key=lambda x: x.overlap, reverse=True)
    else:
        logger.debug("Processing overlap in plate")
        segment_overlap = _calc_plate_overlap(
            base_segment=base_segment,
            plate_base=plate_base,
            match_segment=match_segment,
            plate_match=plate_match,
        )
        if segment_overlap.overlap >= overlap_threshold:
            return [segment_overlap]
        else:
            return []


def _calc_plate_overlap(
    base_segment: GPXTrackSegment,
    plate_base: npt.NDArray,
    match_segment: GPXTrackSegment,
    plate_match: npt.NDArray,
) -> SegmentOverlap:
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

    base_track = GPXTrack()
    base_track.segments = [base_segment]

    first_point_distance_info = get_point_distance(
        base_track, 0, first_point_match.latitude, first_point_match.longitude
    )
    first_point_base, first_idx = (
        first_point_distance_info.point,
        first_point_distance_info.segment_point_idx,
    )

    last_point_distance_info = get_point_distance(
        base_track, 0, last_point_match.latitude, last_point_match.longitude
    )

    last_point_base, last_idx = (
        last_point_distance_info.point,
        last_point_distance_info.segment_point_idx,
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

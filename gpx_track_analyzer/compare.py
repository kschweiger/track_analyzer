from math import pi
from typing import Tuple

import numpy as np
import numpy.typing as npt
from gpxpy.gpx import GPXTrackSegment

from gpx_track_analyzer.model import Position2D
from gpx_track_analyzer.utils import (
    distance,
    get_latitude_at_distance,
    get_longitude_at_distance,
)


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


def get_distances(v1: npt.NDArray, v2: npt.NDArray):
    v1_lats, v1_longs = v1[:, 0], v1[:, 1]
    v2_lats, v2_longs = v2[:, 0], v2[:, 1]

    v1_lats = np.reshape(v1_lats, (v1_lats.shape[0], 1))
    v2_lats = np.reshape(v2_lats, (1, v2_lats.shape[0]))

    v1_longs = np.reshape(v1_longs, (v1_longs.shape[0], 1))
    v2_longs = np.reshape(v2_longs, (1, v2_longs.shape[0]))

    # pi vec
    v_pi = np.reshape(np.ones(v1_lats.shape[0]) * (pi / 180), (v1_lats.shape[0], 1))

    dp = (
        0.5
        - np.cos((v2_lats - v1_lats) * v_pi) / 2
        + np.cos(v1_lats * v_pi)
        * np.cos(v2_lats * v_pi)
        * (1 - np.cos((v2_longs - v1_longs) * v_pi))
        / 2
    )

    dp_km = 12742 * np.arcsin(np.sqrt(dp))

    return dp_km * 1000


def derive_plate_bins(
    gird_width: float,
    bounds_min_latitude: float,
    bounds_min_longitude: float,
    bounds_max_latitude: float,
    bounds_max_longitude: float,
) -> Tuple[list[Tuple[float, float]], list[Tuple[float, float]]]:
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

    lower_edge_latitude = get_latitude_at_distance(
        Position2D(bounds_min_latitude, bounds_min_longitude), gird_width / 2, False
    )
    lower_edge_longitude = get_longitude_at_distance(
        Position2D(bounds_min_latitude, bounds_min_longitude), gird_width / 2, False
    )

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

    return (bins_latitude, bins_longitude)


def convert_segment_to_plate(
    segment: GPXTrackSegment,
    gird_width: float,
    bounds_min_latitude: float,
    bounds_min_longitude: float,
    bounds_max_latitude: float,
    bounds_max_longitude: float,
    normalize: bool = False,
):
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

    for lat, long in zip(segment_lat_bins, segment_long_bins):
        if normalize:
            plate[lat, long] = 1
        else:
            plate[lat, long] += 1

    return np.flip(plate, axis=0)


def get_segment_overlap(s1: GPXTrackSegment, s2: GPXTrackSegment) -> float:
    ...

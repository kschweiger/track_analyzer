from math import pi

import numpy as np
import numpy.typing as npt
from gpxpy.gpx import GPXTrackSegment


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


def get_segment_overlap(s1: GPXTrackSegment, s2: GPXTrackSegment) -> float:
    ...

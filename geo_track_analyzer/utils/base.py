import logging
from datetime import datetime, timedelta
from math import acos, asin, atan2, cos, degrees, pi, sin, sqrt
from typing import Callable, Dict, Union
from xml.etree.ElementTree import Element

import coloredlogs
import numpy as np
import numpy.typing as npt
from gpxpy.gpx import GPXBounds, GPXTrack, GPXTrackPoint, GPXTrackSegment

from geo_track_analyzer.exceptions import (
    GPXPointExtensionError,
    InvalidBoundsError,
    TrackAnalysisError,
)
from geo_track_analyzer.model import (
    ElevationMetrics,
    PointDistance,
    Position2D,
    Position3D,
)

logger = logging.getLogger(__name__)


class ExtensionFieldElement(Element):
    def __init__(self, name: str, text: str) -> None:
        super().__init__(name)
        self.text = text


def distance(pos1: Position2D, pos2: Position2D) -> float:
    """
    Calculate the distance between to long/lat points using the Haversine formula.
    Following: https://stackoverflow.com/a/21623206

    :param pos1: Lat/long position 1
    :param pos2: Lat/long position 2

    :returns: Distance in m
    """
    p = pi / 180
    a = (
        0.5
        - cos((pos2.latitude - pos1.latitude) * p) / 2
        + cos(pos1.latitude * p)
        * cos(pos2.latitude * p)
        * (1 - cos((pos2.longitude - pos1.longitude) * p))
        / 2
    )
    distance_km = 12742 * asin(sqrt(a))
    return distance_km * 1000


def get_latitude_at_distance(
    position: Position2D, distance: float, to_east: bool
) -> float:
    a = pow(sin(distance / 12742000), 2)
    b = acos(1 - 2 * a) / (pi / 180)
    if to_east:
        return b + position.latitude
    return position.latitude - b


def get_longitude_at_distance(
    position: Position2D, distance: float, to_north: bool
) -> float:
    p = pi / 180
    a = pow(sin(distance / 12742000), 2)
    b = pow(cos(position.latitude * p), 2) / 2
    c = acos(1 - (a / b)) / p

    if to_north:
        return c + position.longitude
    return position.longitude - c


def calc_elevation_metrics(
    positions: list[Position3D],
) -> ElevationMetrics:
    """
    Calculate elevation related metrics for the passed list of Position3D objects

    :param positions: Position3D object containing latitude, longitude and elevation

    :returns: A ElevationMetrics object containing uphill and downhill distances and the
        point-to-point slopes.
    """
    uphill = 0.0
    downhill = 0.0
    slopes = [0.0]  # Pad with slope 0 so len(slopes) == len(positions)
    for prev_pos, curr_pos in zip(positions, positions[1::]):  # noqa: RUF007
        if curr_pos == prev_pos:
            continue
        if curr_pos.elevation is None or prev_pos.elevation is None:
            continue

        pp_elevation = curr_pos.elevation - prev_pos.elevation
        pp_distance = distance(prev_pos, curr_pos)

        if pp_elevation > 0:
            uphill += pp_elevation
        else:
            downhill += pp_elevation
        try:
            o_by_h = pp_elevation / pp_distance
        except ZeroDivisionError:
            o_by_h = 0
        # Addressing **ValueError: math domain error**
        if o_by_h > 1 or o_by_h < -1:
            slopes.append(np.NaN)
        else:
            slopes.append(degrees(asin(o_by_h)))

    return ElevationMetrics(uphill, abs(downhill), slopes)


def parse_level(this_level: Union[int, str]) -> tuple[int, Callable]:
    if this_level == 20 or this_level == "INFO":
        return logging.INFO, logging.info
    elif this_level == 10 or this_level == "DEBUG":
        return logging.DEBUG, logging.debug
    elif this_level == 30 or this_level == "WARNING":
        return logging.WARNING, logging.warning
    elif this_level == 40 or this_level == "ERROR":
        return logging.ERROR, logging.error
    elif this_level == 50 or this_level == "CRITICAL":
        return logging.CRITICAL, logging.critical
    else:
        raise RuntimeError("%s is not supported" % this_level)


def init_logging(this_level: Union[int, str]) -> bool:
    """Helper function for setting up python logging"""
    log_format = "[%(asctime)s] %(name)-30s %(levelname)-8s %(message)s"
    level, _ = parse_level(this_level)
    coloredlogs.install(level=level, fmt=log_format)
    return True


def center_geolocation(geolocations: list[tuple[float, float]]) -> tuple[float, float]:
    """
    Calculate an estimated (based on the assumption the earth is a perfect sphere) given
    a list of latitude, longitude pairs in degree.

    Based on: https://gist.github.com/amites/3718961

    :param geolocations: list of latitude, longitude pairs in degree

    :returns: Estimate center latitude, longitude pair in degree
    """
    x, y, z = 0.0, 0.0, 0.0

    for lat, lon in geolocations:
        lat = float(lat) * pi / 180
        lon = float(lon) * pi / 180
        x += cos(lat) * cos(lon)
        y += cos(lat) * sin(lon)
        z += sin(lat)

    x = float(x / len(geolocations))
    y = float(y / len(geolocations))
    z = float(z / len(geolocations))

    lat_c, lon_c = atan2(z, sqrt(x * x + y * y)), atan2(y, x)

    return lat_c * 180 / pi, lon_c * 180 / pi


def interpolate_linear(
    start: GPXTrackPoint, end: GPXTrackPoint, spacing: float
) -> None | list[GPXTrackPoint]:
    """
    Simple linear interpolation between GPXTrackPoint. Supports latitude, longitude
    (required), elevation (optional), and time (optional)
    """

    pp_distance = distance(
        Position2D(start.latitude, start.longitude),
        Position2D(end.latitude, end.longitude),
    )
    if pp_distance < 2 * spacing:
        return None

    logger.debug(
        "pp-distance %s | n_points interpol %s ", pp_distance, pp_distance // spacing
    )

    fracs = np.arange(0, (pp_distance // spacing) + 1)
    lat_int = np.interp(
        fracs, [0, pp_distance // spacing], [start.latitude, end.latitude]
    )
    lng_int = np.interp(
        fracs, [0, pp_distance // spacing], [start.longitude, end.longitude]
    )

    if start.elevation is None or end.elevation is None:
        elevation_int = len(lng_int) * [None]
    else:
        elevation_int = np.interp(
            fracs, [0, pp_distance // spacing], [start.elevation, end.elevation]
        )

    if start.time is None or end.time is None:
        time_int = len(lng_int) * [None]
    else:
        time_int = np.interp(
            fracs,
            [0, pp_distance // spacing],
            [0, (end.time - start.time).total_seconds()],
        )

    ret_points = []

    for lat, lng, ele, seconds in zip(lat_int, lng_int, elevation_int, time_int):
        if seconds is not None:
            time = start.time + timedelta(seconds=seconds)
        else:
            time = None
        ret_points.append(
            GPXTrackPoint(
                lat,
                lng,
                elevation=ele,
                time=time,
            )
        )
        logger.debug(
            "New point %s / %s / %s / %s -> distance to origin %s",
            lat,
            lng,
            ele,
            time,
            distance(
                Position2D(start.latitude, start.longitude),
                Position2D(lat, lng),
            ),
        )

    return ret_points


def interpolate_segment(segment: GPXTrackSegment, spacing: float) -> GPXTrackSegment:
    """
    Interpolate points in a GPXTrackSegment to achieve a specified spacing.

    :param segment: GPXTrackSegment to interpolate.
    :param spacing: Desired spacing between interpolated points.

    :return: Interpolated GPXTrackSegment with points spaced according to the specified
        spacing.
    """
    init_points = segment.points

    new_segment_points = []
    for i, (start, end) in enumerate(
        zip(init_points[:-1], init_points[1:])  # noqa: RUF007
    ):
        new_points = interpolate_linear(
            start=start,
            end=end,
            spacing=spacing,
        )

        if new_points is None:
            if i == 0:
                new_segment_points.extend([start, end])
            else:
                new_segment_points.extend([end])
            continue

        if i == 0:
            new_segment_points.extend(new_points)
        else:
            new_segment_points.extend(new_points[1:])

    interpolated_segment = GPXTrackSegment()
    interpolated_segment.points = new_segment_points
    return interpolated_segment


def get_segment_base_area(segment: GPXTrackSegment) -> float:
    """Caculate the area enclodes by the bounds in m^2"""
    bounds = segment.get_bounds()

    try:
        check_bounds(bounds)
    except InvalidBoundsError:
        return 0

    # After check_bounds this always works
    latitude_distance = distance(
        Position2D(bounds.max_latitude, bounds.min_longitude),  # type: ignore
        Position2D(bounds.min_latitude, bounds.min_longitude),  # type: ignore
    )

    longitude_distance = distance(
        Position2D(bounds.min_latitude, bounds.max_longitude),  # type: ignore
        Position2D(bounds.min_latitude, bounds.min_longitude),  # type: ignore
    )

    return latitude_distance * longitude_distance


def crop_segment_to_bounds(
    segment: GPXTrackSegment,
    bounds_min_latitude: float,
    bounds_min_longitude: float,
    bounds_max_latitude: float,
    bounds_max_longitude: float,
) -> GPXTrackSegment:
    """
    Crop a GPXTrackSegment to include only points within specified geographical bounds.

    :param segment: GPXTrackSegment to be cropped.
    :param bounds_min_latitude: Minimum latitude of the geographical bounds.
    :param bounds_min_longitude: Minimum longitude of the geographical bounds.
    :param bounds_max_latitude: Maximum latitude of the geographical bounds.
    :param bounds_max_longitude: Maximum longitude of the geographical bounds.

    :return: Cropped GPXTrackSegment containing only points within the specified bounds.
    """
    cropped_segment = GPXTrackSegment()
    for point in segment.points:
        if (bounds_min_latitude <= point.latitude <= bounds_max_latitude) and (
            bounds_min_longitude <= point.longitude <= bounds_max_longitude
        ):
            cropped_segment.points.append(point)

    return cropped_segment


def get_distances(v1: npt.NDArray, v2: npt.NDArray) -> npt.NDArray:
    """
    Calculates the distances between two sets of latitude/longitude pairs.

    :param v1: A NumPy array of shape (N, 2) containing latitude/longitude pairs.
    :param v2: A NumPy array of shape (N, 2) containing latitude/longitude pairs.

    :return: A NumPy array of shape (N, M) containing the distances between the
        corresponding pairs in v1 and v2.
    """
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
        - np.cos((v2_lats - v1_lats) * v_pi) / 2  # type: ignore
        + np.cos(v1_lats * v_pi)  # type: ignore
        * np.cos(v2_lats * v_pi)  # type: ignore
        * (1 - np.cos((v2_longs - v1_longs) * v_pi))  # type: ignore
        / 2
    )

    dp_km = 12742 * np.arcsin(np.sqrt(dp))

    return dp_km * 1000


def get_point_distance(
    track: GPXTrack, segment_idx: None | int, latitude: float, longitude: float
) -> PointDistance:
    """
    Calculates the distance to the nearest point on a GPX track.

    :param track: The GPX track to analyze.
    :param segment_idx: The index of the segment to analyze. If None, all segments are
        analyzed.
    :param latitude: The latitude of the point to compare against.
    :param longitude: The longitude of the point to compare against.
    :raises TrackAnalysisError: If the nearest point could not be determined.

    :return: PointDistance: The calculated distance to the nearest point on the track.
    """
    points: list[tuple[float, float]] = []
    segment_point_idx_map: dict[int, tuple[int, int]] = {}
    if segment_idx is None:
        for i_segment, segment in enumerate(track.segments):
            first_idx = len(points)
            for point in segment.points:
                points.append((point.latitude, point.longitude))
            last_idx = len(points) - 1

            segment_point_idx_map[i_segment] = (first_idx, last_idx)
    else:
        segment = track.segments[segment_idx]
        for point in segment.points:
            points.append((point.latitude, point.longitude))

        segment_point_idx_map[segment_idx] = (0, len(points) - 1)

    distances = get_distances(np.array(points), np.array([[latitude, longitude]]))

    _min_idx = int(distances.argmin())
    min_distance = float(distances.min())
    _min_point = None
    _min_segment = -1
    _min_idx_in_segment = -1
    for i_seg, (i_min, i_max) in segment_point_idx_map.items():
        if i_min <= _min_idx <= i_max:
            _min_idx_in_segment = _min_idx - i_min
            _min_point = track.segments[i_seg].points[_min_idx_in_segment]
            _min_segment = i_seg
    if _min_point is None:
        raise TrackAnalysisError("Point could not be determined")

    return PointDistance(
        point=_min_point,
        distance=min_distance,
        point_idx_abs=_min_idx,
        segment_idx=_min_segment,
        segment_point_idx=_min_idx_in_segment,
    )


def get_points_inside_bounds(
    segment: GPXTrackSegment,
    bounds_min_latitude: float,
    bounds_min_longitude: float,
    bounds_max_latitude: float,
    bounds_max_longitude: float,
) -> list[tuple[int, bool]]:
    """
    Get a list of tuples representing points inside or outside a specified geographical
    bounds.

    :param segment: GPXTrackSegment to analyze.
    :param bounds_min_latitude: Minimum latitude of the geographical bounds.
    :param bounds_min_longitude: Minimum longitude of the geographical bounds.
    :param bounds_max_latitude: Maximum latitude of the geographical bounds.
    :param bounds_max_longitude: Maximum longitude of the geographical bounds.

    :return: List of tuples containing index and a boolean indicating whether the point
        is inside the bounds.
    """
    ret_list = []
    for idx, point in enumerate(segment.points):
        inside_bounds = (
            bounds_min_latitude <= point.latitude <= bounds_max_latitude
        ) and (bounds_min_longitude <= point.longitude <= bounds_max_longitude)
        ret_list.append((idx, inside_bounds))

    return ret_list


def split_segment_by_id(
    segment: GPXTrackSegment, index_ranges: list[tuple[int, int]]
) -> list[GPXTrackSegment]:
    """
    Split a GPXTrackSegment into multiple segments based on the provided index ranges.

    :param segment: GPXTrackSegment to be split.
    :param index_ranges: List of tuples representing index ranges for splitting the
        segment.

    :return: List of GPXTrackSegments resulting from the split.
    """
    ret_segments = []

    indv_idx: list[int] = []
    range_classifiers = []
    for range_ in index_ranges:
        indv_idx.extend(list(range_))
        range_classifiers.append(lambda i, le=range_[0], re=range_[1]: le <= i <= re)
        ret_segments.append(GPXTrackSegment())

    min_idx = min(indv_idx)
    max_idx = max(indv_idx)

    for idx, point in enumerate(segment.points):
        if idx < min_idx or idx > max_idx:
            continue

        for i_class, func in enumerate(range_classifiers):
            if func(idx):
                ret_segments[i_class].points.append(point)

    return ret_segments


def check_bounds(bounds: None | GPXBounds) -> None:
    """
    Check if the provided GPXBounds object is valid.

    :param bounds: GPXBounds object to be checked.
    :raises InvalidBoundsError: If the bounds object is None or has incomplete
        latitude/longitude values.
    """
    if bounds is None:
        raise InvalidBoundsError("Bounds %s are invalid", bounds)

    if (
        bounds.min_latitude is None
        or bounds.max_latitude is None
        or bounds.min_longitude is None
        or bounds.max_longitude is None
    ):
        raise InvalidBoundsError("Bounds %s are invalid", bounds)


def get_extension_value(point: GPXTrackPoint, key: str) -> str:
    for ext in point.extensions:
        if ext.tag == key:
            if ext.text is None:
                GPXPointExtensionError("Key %s was not initilized with a value" % key)
            return ext.text  # type: ignore

    raise GPXPointExtensionError("Key %s could not be found" % key)


def get_extended_track_point(
    lat: float,
    lng: float,
    ele: None | float,
    timestamp: None | datetime,
    extensions: Dict[str, Union[str, float, int]],
) -> GPXTrackPoint:
    """
    Create a GPXTrackPoint with extended data fields.

    :param lat: Latitude of the track point.
    :param lng: Longitude of the track point.
    :param ele: Elevation of the track point (None if not available).
    :param timestamp: Timestamp of the track point (None if not available).
    :param extensions: Dictionary of extended data fields (key-value pairs).

    :return: GPXTrackPoint with specified attributes and extended data fields.
    """
    this_point = GPXTrackPoint(lat, lng, elevation=ele, time=timestamp)
    for key, value in extensions.items():
        this_point.extensions.append(ExtensionFieldElement(name=key, text=str(value)))

    return this_point


def format_timedelta(td: timedelta) -> str:
    """
    Format a timedelta object as a string in HH:MM:SS format.

    :param td: Timedelta object to be formatted.

    :return: Formatted string representing the timedelta in HH:MM:SS format.
    """
    seconds = td.seconds
    hours = int(seconds / 3600)
    seconds -= hours * 3600
    minutes = int(seconds / 60)
    seconds -= minutes * 60

    if td.days > 0:
        hours += 24 * td.days

    return "{0:02d}:{1:02d}:{2:02d}".format(hours, minutes, seconds)

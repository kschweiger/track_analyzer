import logging
from datetime import timedelta
from math import acos, asin, atan2, cos, degrees, pi, sin, sqrt
from typing import Callable, List, Optional, Tuple, Union

import coloredlogs
import numpy as np
from gpxpy.gpx import GPXTrackPoint, GPXTrackSegment

from gpx_track_analyzer.model import ElevationMetrics, Position2D, Position3D

logger = logging.getLogger(__name__)


def distance(pos1: Position2D, pos2: Position2D) -> float:
    """
    Calculate the distance between to long/lat points using the Haversine formula.
    Following: https://stackoverflow.com/a/21623206

    Returns: Distance in m

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
    else:
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
    else:
        return position.longitude - c


def calc_elevation_metrics(
    positions: List[Position3D],
) -> ElevationMetrics:
    """
    Calculate elevation related metrics for the passed list of Position3D objects

    Args:
        positions: Position3D object containing latitude, longitude and elevation

    Returns: A ElevationMetrics object containing uphill and downhill distances and the
             point-to-point slopes.
    """
    uphill = 0.0
    downhill = 0.0
    slopes = [0.0]  # Pad with slope 0 so len(slopes) == len(positions)
    for prev_pos, curr_pos in zip(positions, positions[1::]):
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

        o_by_h = pp_elevation / pp_distance
        # Addressing **ValueError: math domain error**
        if o_by_h > 1 or o_by_h < -1:
            slopes.append(np.NaN)
        else:
            slopes.append(degrees(asin(o_by_h)))

    return ElevationMetrics(uphill, abs(downhill), slopes)


def parse_level(this_level: Union[int, str]) -> Tuple[int, Callable]:
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


def center_geolocation(geolocations: List[Tuple[float, float]]):
    """
    Calculate an estimated (based on the assumption the earth is a perfect sphere) given
    a list of latitude, longitude pairs in degree.

    Based on: https://gist.github.com/amites/3718961

    Args:
        geolocations: List of latitude, longitude pairs in degree

    Returns: Estimate center latitude, longitude pair in degree
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
) -> Optional[List[GPXTrackPoint]]:
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


def hex_to_RGB(hex: str):
    """
    Pass a hex color name (as string) and get the RGB value

    Source: https://medium.com/@BrendanArtley/matplotlib-color-gradients-21374910584b

    >> hex_to_RGB("#FFFFFF") -> [255,255,255]
    """
    return tuple([int(hex[i : i + 2], 16) for i in range(1, 6, 2)])


def get_color_gradient(c1: str, c2: str, n: int):
    """
    Create a color gradient between two passed colors with N steps.

    Source: https://medium.com/@BrendanArtley/matplotlib-color-gradients-21374910584b
    """
    assert n > 1
    c1_rgb = np.array(hex_to_RGB(c1)) / 255
    c2_rgb = np.array(hex_to_RGB(c2)) / 255
    mix_pcts = [x / (n - 1) for x in range(n)]
    rgb_colors = [((1 - mix) * c1_rgb + (mix * c2_rgb)) for mix in mix_pcts]
    return [
        ("#" + "".join([format(int(round(val * 255)), "02x") for val in item])).upper()
        for item in rgb_colors
    ]


def get_segment_base_area(segment: GPXTrackSegment):
    """Caculate the area enclodes by the bounds in m^2"""
    bounds = segment.get_bounds()

    latitude_distance = distance(
        Position2D(bounds.max_latitude, bounds.min_longitude),
        Position2D(bounds.min_latitude, bounds.min_longitude),
    )

    longitude_distance = distance(
        Position2D(bounds.min_latitude, bounds.max_longitude),
        Position2D(bounds.min_latitude, bounds.min_longitude),
    )

    return latitude_distance * longitude_distance


def crop_segment_to_bounds(
    segment: GPXTrackSegment,
    bounds_min_latitude,
    bounds_min_longitude,
    bounds_max_latitude,
    bounds_max_longitude,
) -> GPXTrackSegment:

    cropped_segment = GPXTrackSegment()
    for point in segment.points:
        if (bounds_min_latitude <= point.latitude <= bounds_max_latitude) and (
            bounds_min_longitude <= point.longitude <= bounds_max_longitude
        ):
            cropped_segment.points.append(point)

    return cropped_segment

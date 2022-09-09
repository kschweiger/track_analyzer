import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import gpxpy
import numpy as np
import pandas as pd
from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint, GPXTrackSegment

from gpx_track_analyzer.exceptions import (
    TrackInitializationException,
    TrackTransformationException,
)
from gpx_track_analyzer.model import Position3D, SegmentOverview
from gpx_track_analyzer.utils import calc_elevation_metrics, interpolate_linear

logger = logging.getLogger(__name__)


class Track(ABC):
    def __init__(
        self, stopped_speed_threshold: float = 1, max_speed_percentile: int = 95
    ):
        logger.debug(
            "Using threshold for stopped speed: %s km/h", stopped_speed_threshold
        )
        logger.debug("Using %s percentile to calculate overview", max_speed_percentile)

        self.stopped_speed_threshold = stopped_speed_threshold
        self.max_speed_percentile = max_speed_percentile

        # Features computed from the tracks
        self.ascent_boundaries: Dict[int, List[Tuple[int, int]]] = {}
        self.descent_boundaries: Dict[int, List[Tuple[int, int]]] = {}

        self.peaks: Dict[int, List[int]] = {}
        self.valleys: Dict[int, List[int]] = {}

        self.global_max_elevation_point: Dict[int, int] = {}
        self.global_min_elevation_point: Dict[int, int] = {}

    @property
    @abstractmethod
    def track(self) -> GPXTrack:
        ...

    @property
    def n_segments(self) -> int:
        return len(self.track.segments)

    def get_xml(self, name: Optional[str] = None, email: Optional[str] = None) -> str:
        gpx = GPX()

        gpx.tracks = [self.track]
        gpx.author_name = name
        gpx.author_email = email

        return gpx.to_xml()

    def get_segment_overview(self, n_segment: int = 0) -> SegmentOverview:
        """
        Get overall metrics for a segment

        Args:
            n_segment: Index of the segment the overview should be generated for

        Returns: A SegmentOverview object containing the metrics
        """
        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            data,
        ) = self._get_processed_data_for_segment(
            self.track.segments[n_segment], self.stopped_speed_threshold
        )

        total_time = time + stopped_time
        total_distance = distance + stopped_distance

        max_speed = None
        avg_speed = None

        if self.track.segments[n_segment].has_times():
            data = self._apply_outlier_cleaning(data)

            max_speed = data.speed[data.in_speed_percentile].max()
            avg_speed = data.speed[data.in_speed_percentile].mean()

        max_elevation = None
        min_elevation = None

        uphill = None
        downhill = None

        if not data.elevation.isna().all():
            max_elevation = data.elevation.max()
            min_elevation = data.elevation.min()
            position_3d = [
                Position3D(rec["latitude"], rec["longitude"], rec["elevation"])
                for rec in data.to_dict("records")
                if not np.isnan(rec["elevation"])
            ]
            elevation_metrics = calc_elevation_metrics(position_3d)

            uphill = elevation_metrics.uphill
            downhill = elevation_metrics.downhill

        overview = SegmentOverview(
            time,
            total_time,
            distance,
            total_distance,
            max_speed,
            avg_speed,
            max_elevation,
            min_elevation,
            uphill,
            downhill,
        )

        return overview

    def get_segment_data(
        self,
        n_segment: int = 0,
        include_all_points: bool = False,
    ):
        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            data,
        ) = self._get_processed_data_for_segment(
            self.track.segments[n_segment],
            self.stopped_speed_threshold,
            include_all_points,
        )

        if self.track.segments[n_segment].has_times():
            data = self._apply_outlier_cleaning(data)

        return data

    def interpolate_points_in_segment(self, spacing: float, n_segment: int = 0) -> None:
        """
        Add additdion points to a segment by interpolating along the direct line
        between each point pair according to the passed spacing parameter

        :param spacing: Minimum distance between points added by the interpolation
        :param n_segment: segment in the track to use, defaults to 0
        """
        init_points = self.track.segments[n_segment].points

        new_segment_points = []
        for i, (start, end) in enumerate(zip(init_points[:-1], init_points[1:])):
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
        self.track.segments[n_segment].points = new_segment_points

    def get_point_data_in_segmnet(
        self, n_segment: int = 0
    ) -> Tuple[List[Tuple[float, float]], Optional[float], Optional[datetime]]:

        coords = []
        elevations = []
        times = []

        for point in self.track.segments[n_segment].points:
            coords.append((point.latitude, point.longitude))
            if point.elevation is not None:
                elevations.append(point.elevation)
            if point.time is not None:
                times.append(point.time)

        if not elevations:
            elevations = None
        elif len(coords) != len(elevations):
            raise TrackTransformationException(
                "Elevation is not set for all points. This is not supported"
            )
        if not times:
            times = None
        elif len(coords) != len(times):
            raise TrackTransformationException(
                "Elevation is not set for all points. This is not supported"
            )

        return coords, elevations, times

    def _apply_outlier_cleaning(self, data: pd.DataFrame) -> pd.DataFrame:

        speed_percentile = np.percentile(
            [s for s in data.speed[data.speed.notna()].to_list()],
            self.max_speed_percentile,
        )

        data_ = data.copy()

        data_["in_speed_percentile"] = data_.apply(
            lambda c: c.speed <= speed_percentile, axis=1
        )

        return data_

    def _get_processed_data_for_segment(
        self,
        segment: GPXTrackSegment,
        stopped_speed_threshold: float = 1,
        include_all_points: bool = False,
    ) -> Tuple[float, float, float, float, pd.DataFrame]:
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

        data: Dict[str, List[Optional[Union[float, bool]]]] = {
            "latitude": [],
            "longitude": [],
            "elevation": [],
            "speed": [],
            "distance": [],
            "distance_2d": [],
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
            ) = self._get_processed_data_w_time(
                segment, data, threshold_ms, include_all_points
            )
        else:
            distance, data = self._get_processed_data_wo_time(
                segment, data, include_all_points
            )
            time, stopped_distance, stopped_time = 0, 0, 0

        data_df = pd.DataFrame(data)

        return (time, distance, stopped_time, stopped_distance, data_df)

    def _get_processed_data_w_time(
        self,
        segment: GPXTrackSegment,
        data: Dict[str, List[Any]],
        threshold_ms: float,
        include_all_points: bool = False,
    ) -> Tuple[float, float, float, float, Dict[str, List[Any]]]:

        time = 0.0
        stopped_time = 0.0

        distance = 0.0
        stopped_distance = 0.0

        cum_distance = 0
        cum_moving = 0
        cum_stopped = 0

        if include_all_points:
            data["latitude"].append(segment.points[0].latitude)
            data["longitude"].append(segment.points[0].longitude)
            data["elevation"].append(segment.points[0].elevation)
            data["speed"].append(None)
            data["distance"].append(None)
            data["distance_2d"].append(None)
            data["cum_distance"].append(None)
            data["cum_distance_moving"].append(None)
            data["cum_distance_stopped"].append(None)
            data["moving"].append(None)

        for previous, point in zip(segment.points, segment.points[1:]):
            # Ignore first and last point
            if point.time and previous.time:
                timedelta = point.time - previous.time

                point_distance_2d = point.distance_2d(previous)
                if point.elevation and previous.elevation:
                    point_distance = point.distance_3d(previous)
                else:
                    point_distance = point_distance_2d
                seconds = timedelta.total_seconds()
                if seconds > 0 and point_distance is not None:
                    if point_distance:

                        is_stopped = (
                            True
                            if (point_distance / seconds) <= threshold_ms
                            else False
                        )

                        data["distance"].append(point_distance)
                        data["distance_2d"].append(point_distance_2d)

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

    def _get_processed_data_wo_time(
        self,
        segment: GPXTrackSegment,
        data: Dict[str, List[Any]],
        include_all_points: bool = False,
    ) -> Tuple[float, Dict[str, List[Any]]]:
        cum_distance = 0
        distance = 0.0

        if include_all_points:
            data["latitude"].append(segment.points[0].latitude)
            data["longitude"].append(segment.points[0].longitude)
            data["elevation"].append(segment.points[0].elevation)
            data["speed"].append(None)
            data["distance"].append(None)
            data["distance_2d"].append(None)
            data["cum_distance"].append(None)
            data["cum_distance_moving"].append(None)
            data["cum_distance_stopped"].append(None)
            data["moving"].append(None)

        for previous, point in zip(segment.points, segment.points[1:]):
            if point.elevation and previous.elevation:
                point_distance = point.distance_3d(previous)
            else:
                point_distance = point.distance_2d(previous)
            if point_distance is not None:
                distance += point_distance

                data["distance"].append(point_distance)
                data["distance_2d"].append(point_distance)
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

    def find_ascents_descents(
        self,
        segment_data: Optional[pd.DataFrame],
        n_segment: int = 0,
        min_elevation_diff_in_section: float = 50,  # TODO: Class Attr?
        max_flat_distance_in_section: float = 10,  # TODO: Class Attr?
        min_elevation_diff_slope: float = 10,  # TODO: Class Attr?
    ) -> None:
        if segment_data is None:
            segment_data = self.get_segment_data(n_segment, False, True)

        self.find_peaks_valleys(
            segment_data,
            n_segment=n_segment,
            min_elevation_diff_in_section=min_elevation_diff_in_section,
            max_flat_distance_in_section=max_flat_distance_in_section,
            min_elevation_diff_slope=min_elevation_diff_slope,
        )

        data = segment_data[segment_data.moving].copy()

        def calc_cum_elevation_between_pois(
            data: pd.DataFrame, idx_1: int, idx_2: int
        ) -> float:
            relevant_data = data.iloc[idx_1:idx_2]
            rcrds = relevant_data.to_dict("records")
            prev_ele = rcrds[0]["elevation"]
            cum_ele = 0.0
            for rcrd in rcrds[1:]:
                cum_ele += rcrd["elevation"] - prev_ele
                prev_ele = rcrd["elevation"]

            return cum_ele

        all_pois = sorted(self.peaks[n_segment] + self.valleys[n_segment])

        if not all_pois:
            self.ascent_boundaries[n_segment] = []
            self.descent_boundaries[n_segment] = []
            return None

        prev_poi = all_pois[0]

        ascent_boundaries = []
        descent_boundaries = []

        for poi in all_pois[1:]:
            if prev_poi in self.valleys[n_segment] and poi in self.peaks[n_segment]:
                logger.debug("Ascent with boundaries: %s - %s", prev_poi, poi)
                # Before adding ascent check if it section between valley and peak is
                # flat (aka. Die cumulative elevation is less than pass set parameters
                if (
                    abs(calc_cum_elevation_between_pois(data, prev_poi, poi))
                    >= min_elevation_diff_slope
                ):
                    ascent_boundaries.append((prev_poi, poi))
            if prev_poi in self.peaks[n_segment] and poi in self.valleys[n_segment]:
                logger.debug("Descent with boundaries: %s - %s", prev_poi, poi)
                # Same check as for ascents
                if (
                    abs(calc_cum_elevation_between_pois(data, prev_poi, poi))
                    >= min_elevation_diff_slope
                ):
                    descent_boundaries.append((prev_poi, poi))
            prev_poi = poi
        self.ascent_boundaries[n_segment] = ascent_boundaries
        self.descent_boundaries[n_segment] = descent_boundaries

    def find_peaks_valleys(
        self,
        segment_data: Optional[pd.DataFrame],
        n_segment: int = 0,
        min_elevation_diff_in_section: float = 50,  # TODO: Class Attr?
        max_flat_distance_in_section: float = 10,  # TODO: Class Attr?
        min_elevation_diff_slope: float = 10,  # TODO: Class Attr?
        debug: bool = True,
    ) -> None:
        """
        Find peaks and valleys in the track and save them as class attributes

        Args:
            segment_data: Data of the segment (from get_segment_data method). If None
                          is passed, the data will be retrieved based on the passed
                          value of n_segment.
            n_segment: Segment in the track to be analyzed
            min_elevation_diff_in_section:
            max_flat_distance_in_section:
            min_elevation_diff_slope:
            debug: Enables additional debug logging msgs
        """
        logger.debug("Finding peaks and valleys. Using:")
        logger.debug(
            "  min_elevation_diff_in_section : %s", min_elevation_diff_in_section
        )
        logger.debug(
            "  max_flat_distance_in_section : %s", max_flat_distance_in_section
        )
        logger.debug("  min_elevation_diff_slope : %s", min_elevation_diff_slope)

        if segment_data is None:
            segment_data = self.get_segment_data(n_segment, False, True)

        peaks = []
        valleys = []

        data = segment_data[segment_data.moving].copy()
        data["distance_2d"].fillna(0, inplace=True)
        data["distance"].fillna(0, inplace=True)

        rcrds = data.to_dict("records")

        ele_n_idx = [(i, rcrd["elevation"]) for i, rcrd in enumerate(rcrds)]

        global_max_idx, global_max_ele = max(ele_n_idx, key=lambda x: x[1])
        global_min_idx, global_min_ele = min(ele_n_idx, key=lambda x: x[1])

        self.global_max_elevation_point[n_segment] = global_max_idx
        self.global_min_elevation_point[n_segment] = global_min_idx

        if (global_max_ele - global_min_ele) <= min_elevation_diff_in_section:
            logger.debug(
                "Max (%s) and min (%s) of track are less than min distance set (%s)",
                global_max_ele,
                global_min_ele,
                min_elevation_diff_in_section,
            )
            self.peaks[n_segment] = []
            self.valleys[n_segment] = []
            return None

        prev_ele = rcrds[0]["elevation"]

        cum_distance = 0
        cum_distance_flat = 0
        cum_elevation = 0
        idx_cummulated = 0

        prev_poi_elevation = rcrds[0]["elevation"]
        prev_poi_idx = 0

        last_poi_was_peak = False
        last_poi_was_valley = False

        for idx, rcrd in enumerate(rcrds):
            dist = rcrd["distance_2d"]
            ele = rcrd["elevation"]
            elevation_diff = rcrd["elevation"] - prev_ele
            if abs(elevation_diff) <= min_elevation_diff_slope:
                cum_distance_flat += rcrd["distance_2d"]
            cum_distance += rcrd["distance_2d"]
            prev_cum_elevation = cum_elevation
            cum_elevation += elevation_diff
            if abs(cum_elevation) >= min_elevation_diff_in_section:
                reset = False
                if (
                    prev_cum_elevation - cum_elevation
                ) > 0.9 and cum_elevation >= min_elevation_diff_in_section:
                    if debug:
                        logger.debug("Found peak:")
                        logger.debug(
                            "  idx: %s, distance: %s, elevation: %s", idx, dist, ele
                        )
                        logger.debug("  cum_distance: %s", cum_distance)
                        logger.debug("  cum_distance_flat: %s", cum_distance_flat)
                        logger.debug("  last_poi_was_peak: %s", last_poi_was_peak)
                        logger.debug("  prev_cum_elevation: %s", prev_cum_elevation)
                        logger.debug("  cum_elevation: %s", cum_elevation)
                        logger.debug(
                            "  prev_cum_ele - cum_ele: %s",
                            prev_cum_elevation - cum_elevation,
                        )
                        logger.debug("  prev_poi_idx: %s", prev_poi_idx)
                        logger.debug("  prev_poi_elevation: %s", prev_poi_elevation)
                    if not last_poi_was_peak:
                        peaks.append(idx - 1)
                        if prev_poi_idx not in valleys:
                            valleys.append(prev_poi_idx)
                    else:
                        peaks.pop()
                        peaks.append(idx - 1)
                    last_poi_was_peak = True
                    last_poi_was_valley = False
                    reset = True
                if (prev_cum_elevation - cum_elevation) < -0.9 and cum_elevation < (
                    -1 * min_elevation_diff_in_section
                ):
                    if debug:
                        logger.debug("Found Valley:")
                        logger.debug(
                            "  idx: %s, distance: %s, elevation: %s", idx, dist, ele
                        )
                        logger.debug("  cum_distance: %s", cum_distance)
                        logger.debug("  cum_distance_flat: %s", cum_distance_flat)
                        logger.debug("  last_poi_was_peak: %s", last_poi_was_peak)
                        logger.debug("  prev_cum_elevation: %s", prev_cum_elevation)
                        logger.debug("  cum_elevation: %s", cum_elevation)
                        logger.debug(
                            "  prev_cum_ele - cum_ele: %s",
                            prev_cum_elevation - cum_elevation,
                        )
                        logger.debug("  prev_poi_idx: %s", prev_poi_idx)
                        logger.debug("  prev_poi_elevation: %s", prev_poi_elevation)
                    if not last_poi_was_valley:
                        valleys.append(idx - 1)
                        if prev_poi_idx not in peaks:
                            peaks.append(prev_poi_idx)
                    else:
                        valleys.pop()
                        valleys.append(idx - 1)

                    last_poi_was_peak = False
                    last_poi_was_valley = True
                    reset = True
                if reset:
                    prev_poi_elevation = prev_ele
                    prev_poi_idx = idx - 1
                    cum_elevation = elevation_diff
                    cum_distance = rcrd["distance_2d"]
                    cum_distance_flat = 0

            if (
                cum_distance_flat >= max_flat_distance_in_section
                and abs(cum_elevation) <= 15
            ):
                cum_distance = 0
                cum_elevation = 0
                cum_distance_flat = 0
                idx_cummulated = idx
                prev_poi_idx = idx
                last_poi_was_peak = False
                last_poi_was_valley = False
                prev_poi_elevation = rcrd["elevation"]

            prev_ele = rcrd["elevation"]
        if abs(cum_elevation) >= min_elevation_diff_slope:
            if cum_elevation >= min_elevation_diff_in_section:
                peaks.append(len(rcrds) - 1)
                if prev_poi_idx not in valleys:
                    valleys.append(prev_poi_idx)
            if cum_elevation <= (-1 * min_elevation_diff_in_section):
                valleys.append(len(rcrds) - 1)
                if prev_poi_idx not in peaks:
                    peaks.append(prev_poi_idx)

        self.peaks[n_segment] = peaks
        self.valleys[n_segment] = valleys

        logger.debug("Found the following for segment %s", n_segment)
        logger.debug("  peaks: %s", self.peaks[n_segment])
        logger.debug("  valleys: %s", self.valleys[n_segment])


class FileTrack(Track):
    def __init__(self, gpx_file: str, n_track: int = 0, **kwargs):
        """
        Initialize a Track object from a gpx file

        Args:
            gpx_file: Path to the gpx file.
            n_track: Index of track in the gpx file.
        """
        super().__init__(**kwargs)

        logger.info("Loading gpx track from file %s", gpx_file)

        gpx = self._get_pgx(gpx_file)

        self._track = gpx.tracks[n_track]

    @staticmethod
    def _get_pgx(gpx_file) -> GPX:
        with open(gpx_file, "r") as f:
            gpx = gpxpy.parse(f)
        return gpx

    @property
    def track(self) -> GPXTrack:
        return self._track


class ByteTrack(Track):
    def __init__(self, bytefile, n_track: int = 0, **kwargs):
        super().__init__(**kwargs)

        gpx = gpxpy.parse(bytefile)

        self._track = gpx.tracks[n_track]

    @property
    def track(self) -> GPXTrack:
        return self._track


class PyTrack(Track):
    def __init__(
        self,
        points: List[Tuple[float, float]],
        elevations: Optional[List[float]],
        times: Optional[List[datetime]],
        **kwargs
    ):
        super().__init__(**kwargs)

        if elevations is not None:
            if len(points) != len(elevations):
                raise TrackInitializationException(
                    "Different number of points and elevations was passed"
                )
            elevations_ = elevations
        else:
            elevations_ = len(points) * [None]

        if times is not None:
            if len(points) != len(times):
                raise TrackInitializationException(
                    "Different number of points and times was passed"
                )
            times_ = times
        else:
            times_ = len(points) * [None]

        gpx = GPX()

        gpx_track = GPXTrack()
        gpx.tracks.append(gpx_track)

        gpx_segment = GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for (lat, lng), ele, time in zip(points, elevations_, times_):
            gpx_segment.points.append(GPXTrackPoint(lat, lng, elevation=ele, time=time))

        self._track = gpx.tracks[0]

    @property
    def track(self) -> GPXTrack:
        return self._track

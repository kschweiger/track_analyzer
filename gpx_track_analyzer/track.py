import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import gpxpy
import numpy as np
import pandas as pd
from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint, GPXTrackSegment

from gpx_track_analyzer.exceptions import TrackInitializationException
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

    @property
    @abstractmethod
    def track(self) -> GPXTrack:
        ...

    @property
    def n_segments(self) -> int:
        return len(self.track.segments)

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

    def get_segment_data(self, n_segment: int = 0) -> pd.DataFrame:
        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            data,
        ) = self._get_processed_data_for_segment(
            self.track.segments[n_segment], self.stopped_speed_threshold
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
        self, segment: GPXTrackSegment, stopped_speed_threshold: float = 1
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
            ) = self._get_processed_data_w_time(segment, data, threshold_ms)
        else:
            distance, data = self._get_processed_data_wo_time(segment, data)
            time, stopped_distance, stopped_time = 0, 0, 0

        data_df = pd.DataFrame(data)

        return (time, distance, stopped_time, stopped_distance, data_df)

    def _get_processed_data_w_time(
        self, segment: GPXTrackSegment, data: Dict[str, List[Any]], threshold_ms: float
    ) -> Tuple[float, float, float, float, Dict[str, List[Any]]]:

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
                            True
                            if (point_distance / seconds) <= threshold_ms
                            else False
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

    def _get_processed_data_wo_time(
        self, segment: GPXTrackSegment, data: Dict[str, List[Any]]
    ) -> Tuple[float, Dict[str, List[Any]]]:
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

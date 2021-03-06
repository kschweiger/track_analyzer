import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union

import gpxpy
import numpy as np
import pandas as pd
from gpxpy.gpx import GPX, GPXTrack, GPXTrackSegment

from gpx_track_analyzer.model import Position3D, SegmentOverview
from gpx_track_analyzer.utils import calc_elevation_metrics

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

    def get_segment_data(self, n_segment: int = 0):
        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            data,
        ) = self._get_processed_data_for_segment(
            self.track.segments[n_segment], self.stopped_speed_threshold
        )

        data = self._apply_outlier_cleaning(data)

        return data

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

        time = 0.0
        stopped_time = 0.0

        distance = 0.0
        stopped_distance = 0.0

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

        data_df = pd.DataFrame(data)
        return (time, distance, stopped_time, stopped_distance, data_df)


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

import logging
from abc import ABC, abstractmethod
from typing import List, Tuple

import gpxpy
import numpy as np
from gpxpy.gpx import GPX, GPXTrack, GPXTrackSegment

from gpx_track_analyzer.model import Position2D, Position3D, SegmentOverview
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
            speeds_and_distances,
            position_2d,
            position_3d,
            stopped_time,
            stopped_distance,
        ) = self._get_processed_data_for_segment(
            self.track.segments[n_segment], self.stopped_speed_threshold
        )

        total_time = time + stopped_time
        total_distance = distance + stopped_distance

        speed_percentile = np.percentile(
            [s for s, _ in speeds_and_distances], self.max_speed_percentile
        )

        speeds_in_percentile = [
            s for s, _ in speeds_and_distances if s <= speed_percentile
        ]

        max_speed = max(speeds_in_percentile)

        avg_speed = sum(speeds_in_percentile) / len(speeds_in_percentile)

        max_elevation = None
        min_elevation = None

        uphill = None
        downhill = None

        if position_3d:
            elevations = [p.elevation for p in position_3d]
            max_elevation = max(elevations)
            min_elevation = min(elevations)

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

    def _get_processed_data_for_segment(
        self, segment: GPXTrackSegment, stopped_speed_threshold: float = 1
    ) -> Tuple[
        float,
        float,
        List[Tuple[float, float]],
        List[Position2D],
        List[Position3D],
        float,
        float,
    ]:
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

        speeds_and_distances: List[Tuple[float, float]] = []
        position_2d: List[Position2D] = []
        position_3d: List[Position3D] = []

        threshold_ms = stopped_speed_threshold / 3.6

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
                        if (point_distance / seconds) <= threshold_ms:
                            stopped_time += seconds
                            stopped_distance += point_distance
                        else:
                            time += seconds
                            distance += point_distance
                        if time:
                            speeds_and_distances.append(
                                (
                                    point_distance / seconds,
                                    point_distance,
                                )
                            )
                            position_2d.append(
                                Position2D(point.latitude, point.longitude)
                            )
                            if point.has_elevation():
                                position_3d.append(
                                    Position3D(
                                        point.latitude, point.longitude, point.elevation
                                    )
                                )

        return (
            time,
            distance,
            speeds_and_distances,
            position_2d,
            position_3d,
            stopped_time,
            stopped_distance,
        )


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

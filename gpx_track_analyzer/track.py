import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import gpxpy
import numpy as np
import pandas as pd
from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint, GPXTrackSegment

from gpx_track_analyzer.exceptions import (
    TrackInitializationException,
    TrackTransformationException,
)
from gpx_track_analyzer.model import Position3D, SegmentOverview
from gpx_track_analyzer.processing import get_processed_segment_data
from gpx_track_analyzer.utils import (
    calc_elevation_metrics,
    get_point_distance_in_segment,
    interpolate_linear,
)

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

        self.processed_segment_data: Dict[
            int, Tuple[float, float, float, float, pd.DataFrame]
        ] = {}

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
        ) = self._get_processed_segment_data(n_segment)

        total_time = time + stopped_time
        total_distance = distance + stopped_distance

        max_speed = None
        avg_speed = None

        if self.track.segments[n_segment].has_times():
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

    def get_closest_point(
        self, n_segment: int, latitude: float, longitude: float
    ) -> Tuple[GPXTrackPoint, float, int]:
        return get_point_distance_in_segment(
            self.track.segments[n_segment], latitude, longitude
        )

    def _get_aggregated_pp_distance_in_segmeent(
        self, agg: str, n_segment: int, threshold: float
    ) -> float:
        data = self.get_segment_data(n_segment=n_segment)

        return data[data.distance >= threshold].distance.agg(agg)

    def get_avg_pp_distance_in_segment(
        self, n_segment: int = 0, threshold: float = 10
    ) -> float:
        return self._get_aggregated_pp_distance_in_segmeent(
            "average", n_segment, threshold
        )

    def get_max_pp_distance_in_segment(
        self, n_segment: int = 0, threshold: float = 10
    ) -> float:
        return self._get_aggregated_pp_distance_in_segmeent("max", n_segment, threshold)

    def _get_processed_segment_data(
        self, n_segment: int = 0
    ) -> Tuple[float, float, float, float, pd.DataFrame]:
        if n_segment not in self.processed_segment_data:
            (
                time,
                distance,
                stopped_time,
                stopped_distance,
                data,
            ) = get_processed_segment_data(
                self.track.segments[n_segment], self.stopped_speed_threshold
            )

            if self.track.segments[n_segment].has_times():
                data = self._apply_outlier_cleaning(data)

            self.processed_segment_data[n_segment] = (
                time,
                distance,
                stopped_time,
                stopped_distance,
                data,
            )

        return self.processed_segment_data[n_segment]

    def get_segment_data(self, n_segment: int = 0) -> pd.DataFrame:
        _, _, _, _, data = self._get_processed_segment_data(n_segment)

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

        # Reset saved processed data
        if n_segment in self.processed_segment_data:
            logger.debug(
                "Deleting saved processed segment data for segment %s", n_segment
            )
            self.processed_segment_data.pop(n_segment)

    def get_point_data_in_segmnet(
        self, n_segment: int = 0
    ) -> Tuple[
        List[Tuple[float, float]], Optional[List[float]], Optional[List[datetime]]
    ]:
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
            elevations = None  # type: ignore
        elif len(coords) != len(elevations):
            raise TrackTransformationException(
                "Elevation is not set for all points. This is not supported"
            )
        if not times:
            times = None  # type: ignore
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
        elevations: List[Optional[float]],
        times: List[Optional[datetime]],
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

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Sequence, final

import gpxpy
import numpy as np
import pandas as pd
from fitparse import DataMessage, FitFile, StandardUnitsDataProcessor
from gpxpy.gpx import GPX, GPXTrack, GPXTrackSegment

from track_analyzer.compare import get_segment_overlap
from track_analyzer.exceptions import (
    TrackInitializationError,
    TrackTransformationError,
)
from track_analyzer.model import Position3D, SegmentOverview
from track_analyzer.processing import (
    get_processed_segment_data,
    get_processed_track_data,
)
from track_analyzer.utils import (
    PointDistance,
    calc_elevation_metrics,
    get_extended_track_point,
    get_point_distance,
    interpolate_segment,
)

logger = logging.getLogger(__name__)

process_data_tuple_type = tuple[float, float, float, float, pd.DataFrame]


class Track(ABC):
    def __init__(
        self, stopped_speed_threshold: float, max_speed_percentile: int
    ) -> None:
        logger.debug(
            "Using threshold for stopped speed: %s km/h", stopped_speed_threshold
        )
        logger.debug("Using %s percentile to calculate overview", max_speed_percentile)

        self.stopped_speed_threshold = stopped_speed_threshold
        self.max_speed_percentile = max_speed_percentile

        self._processed_segment_data: Dict[int, process_data_tuple_type] = {}
        self._processed_track_data: None | tuple[int, process_data_tuple_type] = None

        self.session_data: Dict[str, str | int | float] = {}

    @property
    @abstractmethod
    def track(self) -> GPXTrack:
        ...

    @property
    def n_segments(self) -> int:
        return len(self.track.segments)

    def add_segmeent(self, segment: GPXTrackSegment) -> None:
        self.track.segments.append(segment)
        logger.info("Added segment with postition: %s", len(self.track.segments))

    def get_xml(self, name: None | str = None, email: None | str = None) -> str:
        gpx = GPX()

        gpx.tracks = [self.track]
        gpx.author_name = name
        gpx.author_email = email

        return gpx.to_xml()

    def get_track_overview(self) -> SegmentOverview:
        """
        Get overall metrics for the track. Equivalent to the sum of all segments

        :return: A SegmentOverview object containing the metrics
        """
        (
            track_time,
            track_distance,
            track_stopped_time,
            track_stopped_distance,
            track_data,
        ) = self._get_processed_track_data()

        track_max_speed = None
        track_avg_speed = None

        if all(seg.has_times() for seg in self.track.segments):
            track_max_speed = track_data.speed[track_data.in_speed_percentile].max()
            track_avg_speed = track_data.speed[track_data.in_speed_percentile].mean()

        return self._create_segment_overview(
            time=track_time,
            distance=track_distance,
            stopped_time=track_stopped_time,
            stopped_distance=track_stopped_distance,
            max_speed=track_max_speed,
            avg_speed=track_avg_speed,
            data=track_data,  # type: ignore
        )

    def get_segment_overview(self, n_segment: int = 0) -> SegmentOverview:
        """
        Get overall metrics for a segment

        Args:
            n_segment: Index of the segment the overview should be generated for

        Returns: A SegmentOverview object containing the metrics moving time and
        distance, total time and distance, maximum and average speed and elevation and
        cummulated uphill, downholl elevation
        """
        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            data,
        ) = self._get_processed_segment_data(n_segment)

        max_speed = None
        avg_speed = None

        if self.track.segments[n_segment].has_times():
            max_speed = data.speed[data.in_speed_percentile].max()
            avg_speed = data.speed[data.in_speed_percentile].mean()

        return self._create_segment_overview(
            time=time,
            distance=distance,
            stopped_time=stopped_time,
            stopped_distance=stopped_distance,
            max_speed=max_speed,
            avg_speed=avg_speed,
            data=data,
        )

    def _create_segment_overview(
        self,
        time: float,
        distance: float,
        stopped_time: float,
        stopped_distance: float,
        max_speed: None | float,
        avg_speed: None | float,
        data: pd.DataFrame,
    ) -> SegmentOverview:
        """Derive overview metrics for a segmeent"""
        total_time = time + stopped_time
        total_distance = distance + stopped_distance

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

        return SegmentOverview(
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

    def get_closest_point(
        self, n_segment: int, latitude: float, longitude: float
    ) -> PointDistance:
        """
        Get closest point in a segment to the passed latitude and longitude

        :param n_segment: Index of the segment
        :param latitude: Latitude to check
        :param longitude: Longitude to check
        :return: Tuple containg the point as GPXTrackPoint, the distance from
        the passed coordinates and the index in the segment
        """
        return get_point_distance(self.track, n_segment, latitude, longitude)

    def _get_aggregated_pp_distance(self, agg: str, threshold: float) -> float:
        data = self.get_track_data()

        return data[data.distance >= threshold].distance.agg(agg)

    def _get_aggregated_pp_distance_in_segment(
        self, agg: str, n_segment: int, threshold: float
    ) -> float:
        data = self.get_segment_data(n_segment=n_segment)

        return data[data.distance >= threshold].distance.agg(agg)

    def get_avg_pp_distance(self, threshold: float = 10) -> float:
        """
        Get average distance between points in the track.

        :param threshold: Minimum distance between points required to  be used for the
        average, defaults to 10
        :return: Average distance
        """
        return self._get_aggregated_pp_distance("average", threshold)

    def get_avg_pp_distance_in_segment(
        self, n_segment: int = 0, threshold: float = 10
    ) -> float:
        """
        Get average distance between points in the segment with index n_segment.

        :param n_segment: Index of the segement to process, defaults to 0
        :param threshold: Minimum distance between points required to  be used for the
        average, defaults to 10
        :return: Average distance
        """
        return self._get_aggregated_pp_distance_in_segment(
            "average", n_segment, threshold
        )

    def get_max_pp_distance(self, threshold: float = 10) -> float:
        """
        Get maximum distance between points in the track.

        :param threshold: Minimum distance between points required to  be used for the
        maximum, defaults to 10
        :return: Maximum distance
        """
        return self._get_aggregated_pp_distance("max", threshold)

    def get_max_pp_distance_in_segment(
        self, n_segment: int = 0, threshold: float = 10
    ) -> float:
        """
        Get maximum distance between points in the segment with index n_segment.

        :param n_segment: Index of the segement to process, defaults to 0
        :param threshold: Minimum distance between points required to  be used for the
        maximum, defaults to 10
        :return: Maximum distance
        """
        return self._get_aggregated_pp_distance_in_segment("max", n_segment, threshold)

    def _get_processed_segment_data(
        self, n_segment: int = 0
    ) -> tuple[float, float, float, float, pd.DataFrame]:
        if n_segment not in self._processed_segment_data:
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

            self._processed_segment_data[n_segment] = (
                time,
                distance,
                stopped_time,
                stopped_distance,
                data,
            )

        return self._processed_segment_data[n_segment]

    def _get_processed_track_data(self) -> process_data_tuple_type:
        if self._processed_track_data:
            segments_in_data, data = self._processed_track_data
            if segments_in_data == self.n_segments:
                return data

        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            data,
        ) = get_processed_track_data(self.track, self.stopped_speed_threshold)

        if all(seg.has_times() for seg in self.track.segments):
            data = self._apply_outlier_cleaning(data)

        return self._set_processed_track_data(
            (
                time,
                distance,
                stopped_time,
                stopped_distance,
                data,
            )
        )

    def _set_processed_track_data(
        self, data: process_data_tuple_type
    ) -> process_data_tuple_type:
        """Save processed data internally to reduce compute.
        Mainly separated for testing"""
        self._processed_track_data = (self.n_segments, data)
        return data

    def get_segment_data(self, n_segment: int = 0) -> pd.DataFrame:
        """Get processed data for the segmeent with passed index as DataFrame

        :param n_segment: Index of the segement, defaults to 0
        :return: DataFrame with segmenet data
        """
        _, _, _, _, data = self._get_processed_segment_data(n_segment)

        return data

    def get_track_data(self) -> pd.DataFrame:
        """
        Get processed data for the track as DataFrame. Segment are indicated
        via the segment column.

        :return: DataFrame with track data
        """
        track_data: None | pd.DataFrame = None

        _, _, _, _, track_data = self._get_processed_track_data()

        return track_data

    def interpolate_points_in_segment(self, spacing: float, n_segment: int = 0) -> None:
        """
        Add additdion points to a segment by interpolating along the direct line
        between each point pair according to the passed spacing parameter

        :param spacing: Minimum distance between points added by the interpolation
        :param n_segment: segment in the track to use, defaults to 0
        """
        self.track.segments[n_segment] = interpolate_segment(
            self.track.segments[n_segment], spacing
        )

        # Reset saved processed data
        if n_segment in self._processed_segment_data:
            logger.debug(
                "Deleting saved processed segment data for segment %s", n_segment
            )
            self._processed_segment_data.pop(n_segment)

    def get_point_data_in_segmnet(
        self, n_segment: int = 0
    ) -> tuple[list[tuple[float, float]], None | list[float], None | list[datetime]]:
        """Get raw coordinates (latitude, longitude), times and elevations for the
        segement with the passed index.

        :param n_segment: Index of the segement, defaults to 0
        :return: tuple with coordinates (latitude, longitude), times and elevations
        """
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
            raise TrackTransformationError(
                "Elevation is not set for all points. This is not supported"
            )
        if not times:
            times = None  # type: ignore
        elif len(coords) != len(times):
            raise TrackTransformationError(
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

    def find_overlap_with_segment(
        self,
        n_segment: int,
        match_track: Track,
        match_track_segment: int = 0,
        width: float = 50,
        overlap_threshold: float = 0.75,
        max_queue_normalize: int = 5,
        merge_subsegments: int = 5,
    ) -> Sequence[tuple[Track, float, bool]]:
        max_distance_self = self.get_max_pp_distance_in_segment(n_segment)

        segment_self = self.track.segments[n_segment]
        if max_distance_self > width:
            segment_self = interpolate_segment(segment_self, width / 2)

        max_distance_match = match_track.get_max_pp_distance_in_segment(
            match_track_segment
        )
        segment_match = match_track.track.segments[match_track_segment]
        if max_distance_match > width:
            segment_match = interpolate_segment(segment_match, width / 2)

        logger.info("Looking for overlapping segments")
        segment_overlaps = get_segment_overlap(
            segment_self,
            segment_match,
            width,
            max_queue_normalize,
            merge_subsegments,
            overlap_threshold,
        )

        matched_tracks: list[tuple[Track, float, bool]] = []
        for overlap in segment_overlaps:
            logger.info("Found: %s", overlap)
            matched_segment = GPXTrackSegment()
            # TODO: Might need to go up to overlap.end_idx + 1?
            matched_segment.points = self.track.segments[n_segment].points[
                overlap.start_idx : overlap.end_idx
            ]
            matched_tracks.append(
                (
                    SegmentTrack(
                        matched_segment,
                        stopped_speed_threshold=self.stopped_speed_threshold,
                        max_speed_percentile=self.max_speed_percentile,
                    ),
                    overlap.overlap,
                    overlap.inverse,
                )
            )
        return matched_tracks


@final
class GPXFileTrack(Track):
    def __init__(
        self,
        gpx_file: str,
        n_track: int = 0,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
    ) -> None:
        """
        Initialize a Track object from a gpx file

        Args:
            gpx_file: Path to the gpx file.
            n_track: Index of track in the gpx file.
        """
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
        )

        logger.info("Loading gpx track from file %s", gpx_file)

        gpx = self._get_gpx(gpx_file)

        self._track = gpx.tracks[n_track]

    @staticmethod
    def _get_gpx(gpx_file: str) -> GPX:
        with open(gpx_file, "r") as f:
            return gpxpy.parse(f)

    @property
    def track(self) -> GPXTrack:
        return self._track


@final
class ByteTrack(Track):
    def __init__(
        self,
        bytefile: bytes,
        n_track: int = 0,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
    ) -> None:
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
        )

        gpx = gpxpy.parse(bytefile)

        self._track = gpx.tracks[n_track]

    @property
    def track(self) -> GPXTrack:
        return self._track


@final
class PyTrack(Track):
    def __init__(
        self,
        points: list[tuple[float, float]],
        elevations: None | list[float],
        times: None | list[datetime],
        heartrate: None | list[int] = None,
        cadence: None | list[int] = None,
        power: None | list[int] = None,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
    ) -> None:
        """A geospacial data track initialized from python objects

        :param points: List of Latitude/Longitude tuples
        :param elevations: Optional list of elevation for each point
        :param times: Optional list of times for each point
        :param heartrate: Optional list of heartrate values for each point
        :param cadence: Optional list of cadence values for each point
        :param power: Optional list of power values for each point
        :raises TrackInitializationError: Raised if number of elevation, time, heatrate,
                                          or cadence values do not match passed points
        """
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
        )

        gpx = GPX()

        gpx_track = GPXTrack()
        gpx.tracks.append(gpx_track)

        gpx_segment = self._create_segmeent(
            points=points,
            elevations=elevations,
            times=times,
            heartrate=heartrate,
            cadence=cadence,
            power=power,
        )

        gpx_track.segments.append(gpx_segment)

        self._track = gpx.tracks[0]

    @property
    def track(self) -> GPXTrack:
        return self._track

    def _create_segmeent(
        self,
        points: list[tuple[float, float]],
        elevations: None | list[float],
        times: None | list[datetime],
        heartrate: None | list[int] = None,
        cadence: None | list[int] = None,
        power: None | list[int] = None,
    ) -> GPXTrackSegment:
        elevations_: list[None] | list[float]
        times_: list[None] | list[datetime]
        heartrate_: list[None] | list[int]
        cadence_: list[None] | list[int]
        power_: list[None] | list[int]

        if elevations is not None:
            if len(points) != len(elevations):
                raise TrackInitializationError(
                    "Different number of points and elevations was passed"
                )
            elevations_ = elevations
        else:
            elevations_ = len(points) * [None]

        if times is not None:
            if len(points) != len(times):
                raise TrackInitializationError(
                    "Different number of points and times was passed"
                )
            times_ = times
        else:
            times_ = len(points) * [None]

        if heartrate is not None:
            if len(points) != len(heartrate):
                raise TrackInitializationError(
                    "Different number of points and heartrate was passed"
                )
            heartrate_ = heartrate
        else:
            heartrate_ = len(points) * [None]

        if cadence is not None:
            if len(points) != len(cadence):
                raise TrackInitializationError(
                    "Different number of points and cadence was passed"
                )
            cadence_ = cadence
        else:
            cadence_ = len(points) * [None]

        if power is not None:
            if len(points) != len(power):
                raise TrackInitializationError(
                    "Different number of points and cadence was passed"
                )
            power_ = power
        else:
            power_ = len(points) * [None]

        gpx_segment = GPXTrackSegment()

        for (lat, lng), ele, time, hr, cad, pw in zip(
            points, elevations_, times_, heartrate_, cadence_, power_
        ):
            this_extensions = {}
            if hr is not None:
                this_extensions["heartrate"] = hr
            if cad is not None:
                this_extensions["cadence"] = cad
            if pw is not None:
                this_extensions["power"] = pw
            this_point = get_extended_track_point(lat, lng, ele, time, this_extensions)

            gpx_segment.points.append(this_point)

        return gpx_segment

    def add_segmeent(  # type: ignore
        self,
        points: list[tuple[float, float]],
        elevations: None | list[float],
        times: None | list[datetime],
        heartrate: None | list[int] = None,
        cadence: None | list[int] = None,
        power: None | list[int] = None,
    ) -> None:
        gpx_segment = self._create_segmeent(
            points=points,
            elevations=elevations,
            times=times,
            heartrate=heartrate,
            cadence=cadence,
            power=power,
        )
        super().add_segmeent(gpx_segment)


@final
class SegmentTrack(Track):
    def __init__(
        self,
        segment: GPXTrackSegment,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
    ) -> None:
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
        )
        gpx = GPX()

        gpx_track = GPXTrack()
        gpx.tracks.append(gpx_track)

        gpx_track.segments.append(segment)

        self._track = gpx.tracks[0]

    @property
    def track(self) -> GPXTrack:
        return self._track


@final
class FITFileTrack(Track):
    def __init__(
        self,
        fit_file: str,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
    ) -> None:
        """
        Load a .fit file and extract the data into a Track object.
        NOTE: Tested with Wahoo devices only
        """
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
        )

        logger.info("Loading gpx track from file %s", fit_file)

        fit_data = FitFile(
            fit_file,
            data_processor=StandardUnitsDataProcessor(),
        )

        points, elevations, times = [], [], []
        heartrates, cadences, powers = [], [], []

        for record in fit_data.get_messages("record"):  # type: ignore
            record: DataMessage  # type: ignore
            lat = record.get_value("position_lat")
            long = record.get_value("position_long")
            ele = record.get_value("enhanced_altitude")
            ts = record.get_value("timestamp")

            hr = record.get_value("heart_rate")
            cad = record.get_value("cadence")
            pw = record.get_value("power")

            if any([v is None for v in [lat, long, ele, ts]]):
                logger.debug(
                    "Found records with None value in lat/long/elevation/timestamp "
                    " - %s/%s/%s/%s",
                    lat,
                    long,
                    ele,
                    ts,
                )
                continue

            points.append((lat, long))
            elevations.append(ele)
            times.append(ts)

            heartrates.append(hr)
            cadences.append(cad)
            powers.append(pw)

        try:
            session_data: DataMessage = list(fit_data.get_messages("session"))[
                -1
            ]  # type: ignore
        except IndexError:
            logger.debug("Could not load session data from fit file")
        else:
            self.session_data = {  # type: ignore
                "start_time": session_data.get_value("start_time"),
                "ride_time": session_data.get_value("total_timer_time"),
                "total_time": session_data.get_value("total_elapsed_time"),
                "distance": session_data.get_value("total_distance"),
                "ascent": session_data.get_value("total_ascent"),
                "descent": session_data.get_value("total_descent"),
                "avg_velocity": session_data.get_value("avg_speed"),
                "max_velocity": session_data.get_value("max_speed"),
            }

        gpx = GPX()

        gpx_track = GPXTrack()
        gpx.tracks.append(gpx_track)

        gpx_segment = GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for (lat, lng), ele, time, hr, cad, pw in zip(
            points, elevations, times, heartrates, cadences, powers
        ):
            this_extensions = {}
            if hr is not None:
                this_extensions["heartrate"] = hr
            if cad is not None:
                this_extensions["cadence"] = cad
            if pw is not None:
                this_extensions["power"] = pw
            this_point = get_extended_track_point(lat, lng, ele, time, this_extensions)

            gpx_segment.points.append(this_point)

        self._track = gpx.tracks[0]

    @property
    def track(self) -> GPXTrack:
        return self._track
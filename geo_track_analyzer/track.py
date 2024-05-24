from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from itertools import pairwise
from typing import Dict, Literal, Sequence, final

import gpxpy
import numpy as np
import pandas as pd
from fitparse import DataMessage, FitFile, StandardUnitsDataProcessor
from gpxpy.gpx import GPX, GPXTrack, GPXTrackSegment
from plotly.graph_objs.graph_objs import Figure

from geo_track_analyzer.compare import get_segment_overlap
from geo_track_analyzer.exceptions import (
    TrackInitializationError,
    TrackTransformationError,
    VisualizationSetupError,
)
from geo_track_analyzer.model import PointDistance, Position3D, SegmentOverview, Zones
from geo_track_analyzer.processing import (
    get_processed_segment_data,
    get_processed_track_data,
)
from geo_track_analyzer.utils.base import (
    calc_elevation_metrics,
    fill_list,
    get_point_distance,
    interpolate_segment,
)
from geo_track_analyzer.utils.internal import get_extended_track_point
from geo_track_analyzer.visualize import (
    plot_segment_box_summary,
    plot_segment_summary,
    plot_segment_zones,
    plot_segments_on_map,
    plot_track_2d,
    plot_track_enriched_on_map,
    plot_track_line_on_map,
    plot_track_with_slope,
    plot_track_zones,
)

logger = logging.getLogger(__name__)

process_data_tuple_type = tuple[float, float, float, float, pd.DataFrame]


class Track(ABC):
    """
    Abstract base container for geospacial Tracks that defines all methods common to
    all Track types.
    """

    def __init__(
        self,
        stopped_speed_threshold: float,
        max_speed_percentile: int,
        heartrate_zones: None | Zones = None,
        power_zones: None | Zones = None,
        cadence_zones: None | Zones = None,
    ) -> None:
        logger.debug(
            "Using threshold for stopped speed: %s km/h", stopped_speed_threshold
        )
        logger.debug("Using %s percentile to calculate overview", max_speed_percentile)

        self.stopped_speed_threshold = stopped_speed_threshold
        self.max_speed_percentile = max_speed_percentile

        self._processed_segment_data: dict[int, process_data_tuple_type] = {}
        self._processed_track_data: dict[str, tuple[int, process_data_tuple_type]] = {}

        self.session_data: Dict[str, str | int | float] = {}

        self.heartrate_zones = heartrate_zones
        self.power_zones = power_zones
        self.cadence_zones = cadence_zones

    @property
    @abstractmethod
    def track(self) -> GPXTrack: ...

    @property
    def n_segments(self) -> int:
        return len(self.track.segments)

    def add_segmeent(self, segment: GPXTrackSegment) -> None:
        """Add a new segment ot the track

        :param segment: GPXTracksegment to be added
        """
        self.track.segments.append(segment)
        logger.info("Added segment with postition: %s", len(self.track.segments))

    def get_xml(self, name: None | str = None, email: None | str = None) -> str:
        """Get track as .gpx file data

        :param name: Optional author name to be added to gpx file, defaults to None
        :param email: Optional auther e-mail address to be added to the gpx file,
            defaults to None

        :return: Content of a gpx file
        """
        gpx = GPX()

        gpx.tracks = [self.track]
        gpx.author_name = name
        gpx.author_email = email

        return gpx.to_xml()

    def get_track_overview(
        self, connect_segments: Literal["full", "forward"] = "forward"
    ) -> SegmentOverview:
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
        ) = self._get_processed_track_data(connect_segments=connect_segments)

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

        :param n_segment: Index of the segment the overview should be generated for,
            default to 0

        :returns: A SegmentOverview object containing the metrics moving time and
            distance, total time and distance, maximum and average speed and elevation
            and cummulated uphill, downholl elevation
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
                Position3D(
                    latitude=rec["latitude"],
                    longitude=rec["longitude"],
                    elevation=rec["elevation"],
                )
                for rec in data.to_dict("records")
                if not np.isnan(rec["elevation"])
            ]
            elevation_metrics = calc_elevation_metrics(position_3d)

            uphill = elevation_metrics.uphill
            downhill = elevation_metrics.downhill

        return SegmentOverview(
            moving_time_seconds=time,
            total_time_seconds=total_time,
            moving_distance=distance,
            total_distance=total_distance,
            max_velocity=max_speed,
            avg_velocity=avg_speed,
            max_elevation=max_elevation,
            min_elevation=min_elevation,
            uphill_elevation=uphill,
            downhill_elevation=downhill,
        )

    def get_closest_point(
        self, n_segment: None | int, latitude: float, longitude: float
    ) -> PointDistance:
        """
        Get closest point in a segment or track to the passed latitude and longitude
        corrdinate

        :param n_segment: Index of the segment. If None is passed the whole track is
            considered
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
                self.track.segments[n_segment],
                self.stopped_speed_threshold,
                heartrate_zones=self.heartrate_zones,
                power_zones=self.power_zones,
                cadence_zones=self.cadence_zones,
            )

            if data.time.notna().any():
                data = self._apply_outlier_cleaning(data)

            self._processed_segment_data[n_segment] = (
                time,
                distance,
                stopped_time,
                stopped_distance,
                data,
            )

        return self._processed_segment_data[n_segment]

    def _get_processed_track_data(
        self, connect_segments: Literal["full", "forward"]
    ) -> process_data_tuple_type:
        if connect_segments in self._processed_track_data:
            segments_in_data, data = self._processed_track_data[connect_segments]
            if segments_in_data == self.n_segments:
                return data

        (
            time,
            distance,
            stopped_time,
            stopped_distance,
            processed_data,
        ) = get_processed_track_data(
            self.track,
            self.stopped_speed_threshold,
            connect_segments=connect_segments,
            heartrate_zones=self.heartrate_zones,
            power_zones=self.power_zones,
            cadence_zones=self.cadence_zones,
        )

        if processed_data.time.notna().any():
            processed_data = self._apply_outlier_cleaning(processed_data)

        return self._set_processed_track_data(
            (
                time,
                distance,
                stopped_time,
                stopped_distance,
                processed_data,
            ),
            connect_segments,
        )

    def _set_processed_track_data(
        self,
        data: process_data_tuple_type,
        connect_segments: Literal["full", "forward"],
    ) -> process_data_tuple_type:
        """Save processed data internally to reduce compute.
        Mainly separated for testing"""
        self._processed_track_data[connect_segments] = (self.n_segments, data)
        return data

    def get_segment_data(self, n_segment: int = 0) -> pd.DataFrame:
        """Get processed data for the segmeent with passed index as DataFrame

        :param n_segment: Index of the segement, defaults to 0

        :return: DataFrame with segmenet data
        """
        _, _, _, _, data = self._get_processed_segment_data(n_segment)

        return data

    def get_track_data(
        self, connect_segments: Literal["full", "forward"] = "forward"
    ) -> pd.DataFrame:
        """
        Get processed data for the track as DataFrame. Segment are indicated
        via the segment column.

        :return: DataFrame with track data
        """
        track_data: None | pd.DataFrame = None

        _, _, _, _, track_data = self._get_processed_track_data(
            connect_segments=connect_segments
        )

        return track_data

    def interpolate_points_in_segment(
        self,
        spacing: float,
        n_segment: int = 0,
        copy_extensions: Literal[
            "copy-forward", "meet-center", "linear"
        ] = "copy-forward",
    ) -> None:
        """
        Add additdion points to a segment by interpolating along the direct line
        between each point pair according to the passed spacing parameter. If present,
        elevation and time will be linearly interpolated. Extensions (Heartrate,
        Cadence, Power) will be interpolated according to value of copy_extensions.
        Optionas are:

        - copy the value from the start point of the interpolation (copy-forward)
        - Use value of start point for first half and last point for second half
          (meet-center)
        - Linear interpolation (linear)


        :param spacing: Minimum distance between points added by the interpolation
        :param n_segment: segment in the track to use, defaults to 0
        :param copy_extensions: How should the extenstion (if present) be defined in the
            interpolated points.
        """
        self.track.segments[n_segment] = interpolate_segment(
            self.track.segments[n_segment], spacing, copy_extensions=copy_extensions
        )

        # Reset saved processed data
        for key in self._processed_track_data.keys():
            self._processed_track_data.pop(key)
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
        speeds = data.speed[data.speed.notna()].to_list()
        if not speeds:
            logger.warning(
                "Trying to apply outlier cleaning to track w/o speed information"
            )
            return data
        speed_percentile = np.percentile(
            data.speed[data.speed.notna()].to_list(),
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
        extensions_interpolation: Literal[
            "copy-forward", "meet-center", "linear"
        ] = "copy-forward",
    ) -> Sequence[tuple[Track, float, bool]]:
        """Find overlap of a segment of the track with a segment in another track.

        :param n_segment: Segment in the track that sould be used as base for the
            comparison
        :param match_track: Track object containing the segment to be matched
        :param match_track_segment: Segment on the passed track that should be matched
            to the segment in this track, defaults to 0
        :param width: Width (in meters) of the grid that will be filled to estimate
            the overalp , defaults to 50
        :param overlap_threshold: Minimum overlap (as fracrtion) required to return the
            overlap data, defaults to 0.75
        :param max_queue_normalize: Minimum number of successive points in the segment
            between two points falling into same plate bin, defaults to 5
        :param merge_subsegments: Number of points between sub segments allowed
            for merging the segments, defaults to 5
        :param extensions_interpolation: How should the extenstion (if present) be
            defined in the interpolated points, defaults to copy-forward

        :return: Tuple containing a Track with the overlapping points, the overlap in
            percent, and the direction of the overlap
        """
        max_distance_self = self.get_max_pp_distance_in_segment(n_segment)

        segment_self = self.track.segments[n_segment]
        if max_distance_self > width:
            segment_self = interpolate_segment(
                segment_self, width / 2, copy_extensions=extensions_interpolation
            )

        max_distance_match = match_track.get_max_pp_distance_in_segment(
            match_track_segment
        )
        segment_match = match_track.track.segments[match_track_segment]
        if max_distance_match > width:
            segment_match = interpolate_segment(
                segment_match, width / 2, copy_extensions=extensions_interpolation
            )

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

    def plot(
        self,
        kind: Literal[
            "profile",
            "profile-slope",
            "map-line",
            "map-line-enhanced",
            "map-segments",
            "zone_summary",
            "segment_zone_summary",
            "segment_box",
            "segment_summary",
        ],
        *,
        segment: None | int | list[int] = None,
        reduce_pp_intervals: None | int = None,
        use_distance_segments: None | float = None,
        **kwargs,
    ) -> Figure:
        """
        Visualize the full track or a single segment.

        :param kind: Kind of plot to be generated

            - profile: Elevation profile of the track. May be enhanced with additional
              information like Velocity, Heartrate, Cadence, and Power. Pass keyword
              args for [`plot_track_2d`][geo_track_analyzer.visualize.plot_track_2d]
            - profile-slope: Elevation profile with slopes between points. Use the
              reduce_pp_intervals argument to reduce the number of slope intervals.
              Pass keyword args for
              [`plot_track_with_slope`][geo_track_analyzer.visualize.plot_track_with_slope]
            - map-line: Visualize coordinates on the map. Pass keyword args for
              [`plot_track_line_on_map`][geo_track_analyzer.visualize.plot_track_line_on_map]
            - map-line-enhanced: Visualize coordinates on the map. Enhance with
              additional information like Elevation, Velocity, Heartrate, Cadence, and
              Power. Pass keyword args for [`plot_track_enriched_on_map`][geo_track_analyzer.visualize.plot_track_enriched_on_map]
            - map-segments: Visualize coordinates on the map split into segments.
              Pass keyword args for
              [`plot_segments_on_map`][geo_track_analyzer.visualize.plot_segments_on_map]
            - zone_summary : Visualize an aggregate (time, distance, speed) value for a
                metric (heartrate, power, cadence) with defined zones. Pass keyword args
                for [`plot_track_zones`][geo_track_analyzer.visualize.plot_track_zones],
                `aggregate` and `metric` are required.
            - segment_zone_summary : Same as "zone_summary" but split aggregate per
                segment [`plot_segment_zones`][geo_track_analyzer.visualize.plot_segment_zones]
            - segment_box : Box plot of a metric (heartrate, power, cadence, speed,
                elevation) per segment. Pass keyword args for [`plot_segments_on_map`][geo_track_analyzer.visualize.plot_segments_on_map]
                `metric` is required.
            - segment_summary : Visualize a aggregate (total_time, total_distance,
                avg_speed, max_speed) per segment. Pass keyword args for [`plot_segment_summary`][geo_track_analyzer.visualize.plot_segment_summary]
                `aggregate` is required.
        :param segment: Select a specific segment, multiple segments or all segmenets,
            defaults to None
        :param reduce_pp_intervals: Optionally pass a distance in m which is used to
            reduce the points in a track, defaults to None
        :param use_distance_segments: Ignore all segments in data and split full track
            into segments with passed cummulated distance in meters. If passed, segment
            arg must be None. Defaults to None.
        :raises VisualizationSetupError: If the plot prequisites are not met

        :return: Figure (plotly)
        """
        from geo_track_analyzer.utils.track import generate_distance_segments

        if use_distance_segments is not None and segment is not None:
            raise VisualizationSetupError(
                f"use_distance_segments {use_distance_segments} cannot be passed with "
                f"segment {segment}."
            )

        valid_kinds = [
            "profile",
            "profile-slope",
            "map-line",
            "map-line-enhanced",
            "map-segments",
            "zone_summary",
            "segment_zone_summary",
            "segment_box",
            "segment_summary",
        ]

        require_elevation = ["profile", "profile-slope"]
        connect_segment_full = ["map-segments"]
        if kind not in valid_kinds:
            raise VisualizationSetupError(
                f"Kind {kind} is not valid. Pass on of {','.join(valid_kinds)}"
            )

        if kind in ["zone_summary", "segment_zone_summary"] and not all(
            key in kwargs.keys() for key in ["metric", "aggregate"]
        ):
            raise VisualizationSetupError(
                f"If {kind} is passed, **metric** and **aggregate** need to be passed"
            )
        if kind in ["segment_box"] and not all(
            key in kwargs.keys() for key in ["metric"]
        ):
            raise VisualizationSetupError(
                f"If {kind} is passed, **metric** needs to be passed"
            )
        if kind in ["segment_summary"] and not all(
            key in kwargs.keys() for key in ["aggregate"]
        ):
            raise VisualizationSetupError(
                f"If {kind} is passed, **metric** needs to be passed"
            )

        if segment is None:
            from geo_track_analyzer.utils.track import extract_track_data_for_plot

            data = extract_track_data_for_plot(
                track=self,
                kind=kind,
                require_elevation=require_elevation,
                intervals=reduce_pp_intervals,
                connect_segments="full" if kind in connect_segment_full else "forward",
            )
        elif isinstance(segment, int):
            from geo_track_analyzer.utils.track import extract_segment_data_for_plot

            data = extract_segment_data_for_plot(
                track=self,
                segment=segment,
                kind=kind,
                require_elevation=require_elevation,
                intervals=reduce_pp_intervals,
            )
        else:
            from geo_track_analyzer.utils.track import (
                extract_multiple_segment_data_for_plot,
            )

            data = extract_multiple_segment_data_for_plot(
                track=self,
                segments=segment,
                kind=kind,
                require_elevation=require_elevation,
                intervals=reduce_pp_intervals,
            )

        if use_distance_segments is not None:
            data = generate_distance_segments(data, use_distance_segments)

        fig: Figure
        if kind == "profile":
            fig = plot_track_2d(data=data, **kwargs)
        elif kind == "profile-slope":
            fig = plot_track_with_slope(data=data, **kwargs)
        elif kind == "map-line":
            fig = plot_track_line_on_map(data=data, **kwargs)
        elif kind == "map-line-enhanced":
            fig = plot_track_enriched_on_map(data=data, **kwargs)
        elif kind == "map-segments":
            fig = plot_segments_on_map(data=data, **kwargs)
        elif kind == "zone_summary":
            fig = plot_track_zones(data=data, **kwargs)
        elif kind == "segment_zone_summary":
            fig = plot_segment_zones(data=data, **kwargs)
        elif kind == "segment_summary":
            fig = plot_segment_summary(data=data, **kwargs)
        elif kind == "segment_box":
            fig = plot_segment_box_summary(data=data, **kwargs)

        return fig

    def split(
        self, coords: tuple[float, float], distance_threshold: float = 20
    ) -> None:
        """
        Split the track at the passed coordinates. The distance_threshold parameter
        defines the maximum distance between the passed coordingates and the closest
        point in the track.

        :param coords: Latitude, Longitude point at which the split should be made
        :param distance_threshold: Maximum distance between coords and closest point,
            defaults to 20

        :raises TrackTransformationError: If distance exceeds threshold
        """
        lat, long = coords
        point_distance = get_point_distance(
            self.track, None, latitude=lat, longitude=long
        )

        if point_distance.distance > distance_threshold:
            raise TrackTransformationError(
                f"Closes point in track has distance {point_distance.distance:.2f}m "
                "from passed coordingates"
            )
        # Split the segment. The closest point should be the first
        # point of the second segment
        pre_segment, post_segment = self.track.segments[
            point_distance.segment_idx
        ].split(point_distance.segment_point_idx - 1)

        self.track.segments[point_distance.segment_idx] = pre_segment
        self.track.segments.insert(point_distance.segment_idx + 1, post_segment)

        self._processed_segment_data = {}
        self._processed_track_data = {}


@final
class GPXFileTrack(Track):
    """Track that should be initialized by loading a .gpx file"""

    def __init__(
        self,
        gpx_file: str,
        n_track: int = 0,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
        heartrate_zones: None | Zones = None,
        power_zones: None | Zones = None,
        cadence_zones: None | Zones = None,
    ) -> None:
        """Initialize a Track object from a gpx file

        :param gpx_file: Path to the gpx file.
        :param n_track: Index of track in the gpx file, defaults to 0
        :param stopped_speed_threshold: Minium speed required for a point to be count
            as moving, defaults to 1
        :param max_speed_percentile: Points with speed outside of the percentile are not
            counted when analyzing the track, defaults to 95
        :param heartrate_zones: Optional heartrate Zones, defaults to None
        :param power_zones: Optional power Zones, defaults to None
        :param cadence_zones: Optional cadence Zones, defaults to None
        """

        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
            heartrate_zones=heartrate_zones,
            power_zones=power_zones,
            cadence_zones=cadence_zones,
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
    """Track that should be initialized from a byte stream"""

    def __init__(
        self,
        bytefile: bytes,
        n_track: int = 0,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
        heartrate_zones: None | Zones = None,
        power_zones: None | Zones = None,
        cadence_zones: None | Zones = None,
    ) -> None:
        """Initialize a Track object from a gpx file

        :param bytefile: Bytestring of a gpx file
        :param n_track: Index of track in the gpx file, defaults to 0
        :param stopped_speed_threshold: Minium speed required for a point to be count
            as moving, defaults to 1
        :param max_speed_percentile: Points with speed outside of the percentile are not
            counted when analyzing the track, defaults to 95
        :param heartrate_zones: Optional heartrate Zones, defaults to None
        :param power_zones: Optional power Zones, defaults to None
        :param cadence_zones: Optional cadence Zones, defaults to None
        """
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
            heartrate_zones=heartrate_zones,
            power_zones=power_zones,
            cadence_zones=cadence_zones,
        )

        gpx = gpxpy.parse(bytefile)

        self._track = gpx.tracks[n_track]

    @property
    def track(self) -> GPXTrack:
        return self._track


@final
class PyTrack(Track):
    """Track that should be initialized from python objects"""

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
        heartrate_zones: None | Zones = None,
        power_zones: None | Zones = None,
        cadence_zones: None | Zones = None,
    ) -> None:
        """A geospacial data track initialized from python objects

        :param points: List of Latitude/Longitude tuples
        :param elevations: Optional list of elevation for each point
        :param times: Optional list of times for each point
        :param heartrate: Optional list of heartrate values for each point
        :param cadence: Optional list of cadence values for each point
        :param power: Optional list of power values for each point
        :param stopped_speed_threshold: Minium speed required for a point to be count
            as moving, defaults to 1
        :param max_speed_percentile: Points with speed outside of the percentile are not
            counted when analyzing the track, defaults to 95
        :param heartrate_zones: Optional heartrate Zones, defaults to None
        :param power_zones: Optional power Zones, defaults to None
        :param cadence_zones: Optional cadence Zones, defaults to None
        :raises TrackInitializationError: Raised if number of elevation, time, heatrate,
            or cadence values do not match passed points
        """
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
            heartrate_zones=heartrate_zones,
            power_zones=power_zones,
            cadence_zones=cadence_zones,
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
    """
    Track that should be initialized by loading a PGXTrackSegment object
    """

    def __init__(
        self,
        segment: GPXTrackSegment,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
        heartrate_zones: None | Zones = None,
        power_zones: None | Zones = None,
        cadence_zones: None | Zones = None,
    ) -> None:
        """Wrap a GPXTrackSegment into a Track object

        :param segment: GPXTrackSegment
        :param stopped_speed_threshold: Minium speed required for a point to be count
            as moving, defaults to 1
        :param max_speed_percentile: Points with speed outside of the percentile are not
            counted when analyzing the track, defaults to 95
        :param heartrate_zones: Optional heartrate Zones, defaults to None
        :param power_zones: Optional power Zones, defaults to None
        :param cadence_zones: Optional cadence Zones, defaults to None
        """
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
            heartrate_zones=heartrate_zones,
            power_zones=power_zones,
            cadence_zones=cadence_zones,
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
class FITTrack(Track):
    """Track that should be initialized by loading a .fit file"""

    def __init__(
        self,
        source: str | bytes,
        stopped_speed_threshold: float = 1,
        max_speed_percentile: int = 95,
        strict_elevation_loading: bool = False,
        heartrate_zones: None | Zones = None,
        power_zones: None | Zones = None,
        cadence_zones: None | Zones = None,
    ) -> None:
        """Load a .fit file and extract the data into a Track object.
        NOTE: Tested with Wahoo devices only

        :param source: Patch to fit file or byte representation of fit file
        :param stopped_speed_threshold: Minium speed required for a point to be count
            as moving, defaults to 1
        :param max_speed_percentile: Points with speed outside of the percentile are not
            counted when analyzing the track, defaults to 95
        :param strict_elevation_loading: If set, only points are added to the track that
            have a valid elevation,defaults to False
        :param heartrate_zones: Optional heartrate Zones, defaults to None
        :param power_zones: Optional power Zones, defaults to None
        :param cadence_zones: Optional cadence Zones, defaults to None
        """
        super().__init__(
            stopped_speed_threshold=stopped_speed_threshold,
            max_speed_percentile=max_speed_percentile,
            heartrate_zones=heartrate_zones,
            power_zones=power_zones,
            cadence_zones=cadence_zones,
        )

        if isinstance(source, str):
            logger.info("Loading fit track from file %s", source)
        else:
            logger.info("Using passed bytes data as fit track")

        fit_data = FitFile(
            source,
            data_processor=StandardUnitsDataProcessor(),
        )

        points, elevations, times = [], [], []
        heartrates, cadences, powers = [], [], []

        split_at = [0]
        for record in fit_data.get_messages(("record", "lap")):  # type: ignore
            record: DataMessage  # type: ignore
            if record.mesg_type.name == "lap":
                split_at.append(len(points))
            lat = record.get_value("position_lat")
            long = record.get_value("position_long")
            ele = record.get_value("enhanced_altitude")
            ts = record.get_value("timestamp")

            hr = record.get_value("heart_rate")
            cad = record.get_value("cadence")
            pw = record.get_value("power")

            check_vals = [lat, long, ts]
            if strict_elevation_loading:
                check_vals.append(ele)

            if any([v is None for v in check_vals]):
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

        if not strict_elevation_loading and set(elevations) != {None}:
            elevations = fill_list(elevations)

        try:
            session_data: DataMessage = list(fit_data.get_messages("session"))[-1]  # type: ignore
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

        if len(split_at) == 1:
            split_at.append(len(points))

        gpx = GPX()

        gpx_track = GPXTrack()
        gpx.tracks.append(gpx_track)

        for start_idx, end_idx in pairwise(split_at):
            gpx_segment = GPXTrackSegment()

            for (lat, lng), ele, time, hr, cad, pw in zip(
                points[start_idx:end_idx],
                elevations[start_idx:end_idx],
                times[start_idx:end_idx],
                heartrates[start_idx:end_idx],
                cadences[start_idx:end_idx],
                powers[start_idx:end_idx],
            ):
                this_extensions = {}
                if hr is not None:
                    this_extensions["heartrate"] = hr
                if cad is not None:
                    this_extensions["cadence"] = cad
                if pw is not None:
                    this_extensions["power"] = pw
                this_point = get_extended_track_point(
                    lat, lng, ele, time, this_extensions
                )

                gpx_segment.points.append(this_point)

            gpx_track.segments.append(gpx_segment)

        self._track = gpx.tracks[0]

    @property
    def track(self) -> GPXTrack:
        return self._track

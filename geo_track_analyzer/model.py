from typing import Annotated

import numpy as np
from gpxpy.gpx import GPXTrackPoint
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_numpy import np_array_pydantic_annotated_typing

from geo_track_analyzer.utils.internal import GPXTrackPointAfterValidator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Position2D(Model):
    """Position in a 2D latitude / longitude space"""

    latitude: float
    """Latitude of the point"""

    longitude: float
    """Longitude of the point"""


class Position3D(Position2D):
    """Position in a 3D latitude / longitude / elevation space"""

    elevation: None | float
    """Elevation of the point"""


class ElevationMetrics(Model):
    """Collection of elevation related metrics"""

    uphill: float
    """Upill elevation in m"""

    downhill: float
    """Downhill elevation in m"""

    slopes: list[float]
    """Slopes between points in a uphill/downhill section"""


class SegmentOverview(Model):
    """Collection of metrics for a Segment"""

    moving_time_seconds: float
    """Moving time of a segment"""

    total_time_seconds: float
    """Total time of the segment"""

    moving_distance: float
    """Moving distance (point-to-point distance with velocity below a threshold) in m"""

    total_distance: float
    """Total distance of the segment in m"""

    max_velocity: None | float
    """Maximum velocity in the segment in m/s (only considering velocities below the XX
    percentile)"""

    avg_velocity: None | float
    """Average velocity in the segment in m/s (only considering velocities below the XX
    percentile)"""

    max_elevation: None | float
    """Maximum elevation in the segment in m"""

    min_elevation: None | float
    """ Minimum elevation in the segment in m"""

    uphill_elevation: None | float
    """Elevation traveled uphill in m"""

    downhill_elevation: None | float
    """Elevation traveled downhill in m"""

    # Attributes that will be calculated from primary attributes
    moving_distance_km: float = Field(default=-1)
    """moving_distance converted the km"""

    total_distance_km: float = Field(default=-1)
    """total_distance converted the km"""

    max_velocity_kmh: None | float = Field(default=None)
    """max_velocity converted the km/h"""

    avg_velocity_kmh: None | float = Field(default=None)
    """avg_speed converted the km/h"""

    @model_validator(mode="after")
    def set_km_attr(self) -> "SegmentOverview":
        self.moving_distance_km = self.moving_distance / 1000
        self.total_distance_km = self.total_distance / 1000
        self.max_velocity_kmh = (
            None if self.max_velocity is None else 3.6 * self.max_velocity
        )
        self.avg_velocity_kmh = (
            None if self.avg_velocity is None else 3.6 * self.avg_velocity
        )
        return self


class SegmentOverlap(Model):
    """Represent the overlap between two segments"""

    overlap: float
    """Overlap ratio of the segments"""

    inverse: bool
    """Match direction of the segment relative to the base"""

    plate: np_array_pydantic_annotated_typing(data_type=np.float32, dimensions=2)
    """2D representation of the segment overlap"""

    start_point: Annotated[GPXTrackPoint, GPXTrackPointAfterValidator]
    """First point matching the base segment """

    start_idx: int
    """Index of the first point in match segment"""

    end_point: Annotated[GPXTrackPoint, GPXTrackPointAfterValidator]
    """Last point matching the base segment """

    end_idx: int
    """Index of the last point in match segment"""

    def __repr__(self) -> str:
        ret_str = f"Overlap {self.overlap*100:.2f}%, Inverse: {self.inverse},"
        ret_str += f" Plate: {self.plate.shape}, Points: "
        point_strs = []
        for point, idx in zip(
            [self.start_point, self.end_point], [self.start_idx, self.end_idx]
        ):
            point_strs.append(f"({point.latitude},{point.longitude}) at id {idx}")
        ret_str += " to ".join(point_strs)

        return ret_str


class PointDistance(Model):
    """Represents a distance calculati  on to a point in a GPX track."""

    point: Annotated[GPXTrackPoint, GPXTrackPointAfterValidator]
    """The nearest point on the track."""

    distance: float
    """The distance to the nearest point."""

    point_idx_abs: int
    """The absolute index of the nearest point in the track."""

    segment_idx: int
    """The index of the segment containing the nearest point."""

    segment_point_idx: int
    """The index of the nearest point within the containing segment."""

    def __repr__(self) -> str:
        return (
            f"PointDistance(point=({self.point.latitude},{self.point.longitude})"
            f"distance={self.distance}, "
            f"point_idx_abs={self.point_idx_abs}, "
            f"segment_idx={self.segment_idx}, "
            f"segment_point_idx={self.segment_point_idx})"
        )

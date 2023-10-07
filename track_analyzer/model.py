from dataclasses import dataclass, field

import numpy as np
from gpxpy.gpx import GPXTrackPoint


@dataclass
class Position2D:
    latitude: float
    longitude: float


@dataclass
class Position3D(Position2D):
    elevation: None | float


@dataclass
class ElevationMetrics:
    uphill: float
    downhill: float
    slopes: list[float]


@dataclass
class SegmentOverview:
    """
    Collection of metrics for a Segment

    Attributes:
        moving_time_seconds (float): Moving time of a segment
        total_time_seconds (float): Total time of the segment
        moving_distance (float): Moving distance (point-to-point distance with velocity
                                 below a threshold) in m
        total_distance (float): Total distance of the segment in m
        max_velocity (float): Maximum velocity in the segment in m/s (only considering
                           velocities below the XX percentile)
        avg_velocity (float): Average velocity in the segment in m/s (only considering
                           velocities below the XX percentile)
        max_elevation (None | float): Maximum elevation in the segment in m
        min_elevation (None | float): Minimum elevation in the segment in m
        uphill_elevation (None | float): Elevation traveled uphill in m
        downhill_elevation (None | float): Elevation traveled downhill in m
        moving_distance_km (float): moving_distance converted the km
        total_distance_km (float): total_distance converted the km
        max_velocity_kmh (float): max_velocity converted the km/h
        avg_velocity_kmh (float): avg_speed converted the km/h
    """

    moving_time_seconds: float
    total_time_seconds: float

    moving_distance: float
    total_distance: float

    max_velocity: None | float
    avg_velocity: None | float

    max_elevation: None | float
    min_elevation: None | float

    uphill_elevation: None | float
    downhill_elevation: None | float

    # Attributes that will be calculated from primary attributes
    moving_distance_km: None | float = field(init=False)
    total_distance_km: None | float = field(init=False)
    max_velocity_kmh: None | float = field(init=False)
    avg_velocity_kmh: None | float = field(init=False)

    def __post_init__(self) -> None:
        self.moving_distance_km = self.moving_distance / 1000
        self.total_distance_km = self.total_distance / 1000
        self.max_velocity_kmh = (
            None if self.max_velocity is None else 3.6 * self.max_velocity
        )
        self.avg_velocity_kmh = (
            None if self.avg_velocity is None else 3.6 * self.avg_velocity
        )


@dataclass
class SegmentOverlap:
    overlap: float
    inverse: bool
    plate: np.ndarray
    start_point: GPXTrackPoint
    start_idx: int
    end_point: GPXTrackPoint
    end_idx: int

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
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Position2D:
    latitude: float
    longitude: float


@dataclass
class Position3D(Position2D):
    elevation: float


@dataclass
class ElevationMetrics:
    uphill: float
    downhill: float
    slopes: List[float]


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
        max_elevation (float): Maximum elevation in the segment in m
        min_elevation (float): Minimum elevation in the segment in m
        moving_distance_km (float): moving_distance converted the km
        total_distance_km (float): total_distance converted the km
        max_velocity_kmh (float): max_velocity converted the km/h
        avg_velocity_kmh (float): avg_speed converted the km/h
    """

    moving_time_seconds: float
    total_time_seconds: float

    moving_distance: float
    total_distance: float

    max_velocity: float
    avg_velocity: float

    max_elevation: Optional[float]
    min_elevation: Optional[float]

    # Attributes that will be calculated from primary attributes
    moving_distance_km: float = field(init=False)
    total_distance_km: float = field(init=False)
    max_velocity_kmh: float = field(init=False)
    avg_velocity_kmh: float = field(init=False)

    def __post_init__(self):
        self.moving_distance_km = self.moving_distance / 1000
        self.total_distance_km = self.total_distance / 1000
        self.max_velocity_kmh = 3.6 * self.max_velocity
        self.avg_velocity_kmh = 3.6 * self.avg_velocity

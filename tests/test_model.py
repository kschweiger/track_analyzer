import json
from datetime import datetime
from typing import Annotated, Any

import numpy as np
import pytest
from gpxpy.gpx import GPXTrackPoint
from pydantic import ValidationError

from geo_track_analyzer.model import (
    Model,
    PointDistance,
    SegmentOverlap,
    SegmentOverview,
)
from geo_track_analyzer.utils.internal import (
    ExtensionFieldElement,
    GPXTrackPointAfterValidator,
)


class TestModel(Model):
    point: Annotated[GPXTrackPoint, GPXTrackPointAfterValidator]


def test_segment_overview_post_init_calcs() -> None:
    moving_distance = 1000
    total_distance = 12002
    max_speed = 8.333  # 30 km/h
    avg_speed = 5.556  # 20 km/h
    so = SegmentOverview(
        moving_time_seconds=1000,
        total_time_seconds=1000,
        moving_distance=moving_distance,
        total_distance=total_distance,
        max_velocity=max_speed,
        avg_velocity=avg_speed,
        max_elevation=300,
        min_elevation=100,
        uphill_elevation=100,
        downhill_elevation=-200,
    )
    assert so.max_velocity_kmh == max_speed * 3.6
    assert so.avg_velocity_kmh == avg_speed * 3.6
    assert so.moving_distance_km == moving_distance / 1000
    assert so.total_distance_km == total_distance / 1000


def test_point_distance_init() -> None:
    pnt_dst = PointDistance(
        point=GPXTrackPoint(latitude=1.0, longitude=1.0),
        distance=10,
        point_idx_abs=1,
        segment_idx=0,
        segment_point_idx=1,
    )

    assert isinstance(pnt_dst.point, GPXTrackPoint)

    json_data = json.loads(pnt_dst.model_dump_json())

    assert json_data["point"] == {"latitude": 1.0, "longitude": 1.0}


@pytest.mark.parametrize(
    ("point", "exp_dict"),
    [
        (
            GPXTrackPoint(latitude=1.0, longitude=1.0),
            {"latitude": 1.0, "longitude": 1.0},
        ),
        (
            GPXTrackPoint(latitude=1.0, longitude=1.0, elevation=100.0),
            {"latitude": 1.0, "longitude": 1.0, "elevation": 100.0},
        ),
        (
            GPXTrackPoint(
                latitude=1.0,
                longitude=1.0,
                elevation=100.0,
                time=datetime(2024, 1, 1, 12),
            ),
            {
                "latitude": 1.0,
                "longitude": 1.0,
                "elevation": 100.0,
                "time": datetime(2024, 1, 1, 12).isoformat(),
            },
        ),
    ],
)
def test_gpx_validation(point: GPXTrackPoint, exp_dict: dict) -> None:
    assert isinstance(TestModel.model_json_schema(), dict)

    test_model = TestModel(point=point)

    assert test_model.point == point

    json_data = json.loads(test_model.model_dump_json())

    assert json_data["point"] == exp_dict

    model_data = test_model.model_dump()

    for key in model_data["point"].keys():
        if key == "time":
            assert model_data["point"][key].isoformat() == json_data["point"][key]
        else:
            assert model_data["point"][key] == json_data["point"][key]


def test_gpx_with_exstensions() -> None:
    point = GPXTrackPoint(latitude=1.0, longitude=1.0, elevation=100.0)
    point.extensions.append(ExtensionFieldElement(name="heartrate", text="100"))
    point.extensions.append(ExtensionFieldElement(name="cadence", text="80"))
    point.extensions.append(ExtensionFieldElement(name="power", text="300"))

    test_model = TestModel(point=point)

    model_data = test_model.model_dump()

    assert model_data["point"]["heartrate"] == 100.0
    assert model_data["point"]["cadence"] == 80.0
    assert model_data["point"]["power"] == 300.0


@pytest.mark.parametrize(
    "data",
    [{"time": "asds"}, {"time": 1}, {"latitude": "aa"}],
)
def test_gpx_validation_errors(data: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        TestModel.model_validate(data)


def test_segment_overlap_init() -> None:
    test_plate = np.array([[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]])

    overlap = SegmentOverlap(
        overlap=0.8,
        inverse=False,
        plate=test_plate,
        start_point=GPXTrackPoint(latitude=1.0, longitude=1.0),
        start_idx=0,
        end_point=GPXTrackPoint(latitude=2.0, longitude=2.0),
        end_idx=5,
    )

    assert isinstance(overlap.plate, np.ndarray)

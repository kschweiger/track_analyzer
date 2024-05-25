import json
from copy import copy
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
    ZoneInterval,
    Zones,
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
        (
            GPXTrackPoint(latitude=1.0, longitude=1.0, name="some name"),
            {"latitude": 1.0, "longitude": 1.0, "name": "some name"},
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


def test_gep_validation_from_dict() -> None:
    exp = GPXTrackPoint(latitude=1.0, longitude=1.0, elevation=100.0, name="some name")
    test_model = TestModel(
        **{
            "point": {
                "latitude": 1.0,
                "longitude": 1.0,
                "elevation": 100.0,
                "name": "some name",
            }
        }
    )
    for key in ["latitude", "longitude", "elevation", "name"]:
        assert getattr(test_model.point, key) == getattr(exp, key)

    assert not test_model.point.extensions


def test_gep_validation_from_dict_w_ext() -> None:
    exp_extensions = {
        "heartrate": "100.0",
        "power": "300.0",
        "cadence": "80.0",
    }
    test_model = TestModel(
        **{
            "point": {
                "heartrate": 100.0,
                "power": 300.0,
                "cadence": 80.0,
            }
        }
    )

    for ext in test_model.point.extensions:
        for tag, text in copy(exp_extensions).items():
            if ext.tag == tag:
                assert ext.text == text
                exp_extensions.pop(tag)

    assert not exp_extensions


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
    [
        {"point": {"time": "asds"}},
        {"point": {"time": 1}},
        {"point": {"latitude": "a"}},
        {"point": {"bodus": "a"}},
    ],
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


@pytest.mark.parametrize(("start", "end"), [(None, 100), (100, 200), (200, None)])
def test_zone_interval(start: None | int, end: None | int) -> None:
    zi = ZoneInterval(start=start, end=end)
    assert zi.start == start
    assert zi.end == end


def test_zone_interval_start_end_validation() -> None:
    with pytest.raises(ValidationError):
        ZoneInterval(start=None, end=None)


def test_zone_interval_pos_int_validation() -> None:
    with pytest.raises(ValidationError):
        ZoneInterval(start=-10, end=20)


def test_zones() -> None:
    Zones(
        intervals=[
            ZoneInterval(start=None, end=100),
            ZoneInterval(start=100, end=200),
            ZoneInterval(start=200, end=None),
        ]
    )


def test_zones_intervals_validation() -> None:
    with pytest.raises(ValidationError, match="At least two intervals are required"):
        Zones(intervals=[ZoneInterval(start=100, end=200)])


@pytest.mark.parametrize(
    ("first_start", "last_end"), [(50, None), (None, 300), (50, 300)]
)
def test_zones_first_last_interval_model_validation(
    first_start: None | int, last_end: None | int
) -> None:
    with pytest.raises(ValidationError, match=r"(.*) must (.*) with None"):
        Zones(
            intervals=[
                ZoneInterval(start=first_start, end=100),
                ZoneInterval(start=100, end=200),
                ZoneInterval(start=200, end=last_end),
            ]
        )


def test_zones_consecutive_intervals_validation() -> None:
    with pytest.raises(
        ValidationError, match="Consecutive intervals mit start/end with the same value"
    ):
        Zones(
            intervals=[
                ZoneInterval(start=None, end=100),
                ZoneInterval(start=120, end=200),
                ZoneInterval(start=200, end=None),
            ]
        )


def test_zones_names_mixed_error() -> None:
    with pytest.raises(
        ValidationError, match="Set either no names of intervals or all names"
    ):
        Zones(
            intervals=[
                ZoneInterval(start=None, end=100, name="A"),
                ZoneInterval(start=120, end=200),
                ZoneInterval(start=200, end=None),
            ]
        )

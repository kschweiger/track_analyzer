from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from geo_track_analyzer import PyTrack, Track

Coordinates = tuple[float, float, float]


class LineStringGeometry(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[Coordinates]


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: Coordinates


Geometry = Annotated[LineStringGeometry | PointGeometry, Field(discriminator="type")]


class BaseProperties(BaseModel):
    name: str | None = None


class PointProperties(BaseProperties):
    time: datetime
    heartrate: int | None = Field(default=None, alias="heartRate")
    cadence: int | None = None
    power: float | None = None
    temperature: float | None = None


class LineProperties(BaseProperties):
    times: list[datetime] = Field(alias="coordTimes")
    heartrates: list[int | None] | None = Field(default=None, alias="heartRates")
    cadences: list[int | None] | None = None
    powers: list[float | None] | None = None
    temperatures: list[float | None] | None = None


class PointFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry | None = None
    properties: PointProperties


class LineFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: LineStringGeometry | None = None
    properties: LineProperties


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[PointFeature]
    properties: BaseProperties | None = None


def _convert_points_collection(
    data: dict, allow_empty_spatial: bool, fallback_coordinates: tuple[float, float]
) -> Track:
    _data = FeatureCollection.model_validate(data)

    if not allow_empty_spatial and any(g.geometry is None for g in _data.features):
        raise ValueError("One or more features have no geometry")

    points = []
    elevations = []
    times = []
    extensions = dict(
        heartrate=[],
        power=[],
        cadence=[],
        temperature=[],
    )

    for feat in _data.features:
        if allow_empty_spatial:
            pass
            lon, lat = fallback_coordinates
            ele = None
        else:
            assert feat.geometry is not None
            lon, lat, ele = feat.geometry.coordinates
        points.append((lat, lon))
        elevations.append(ele)
        times.append(feat.properties.time)
        extensions["heartrate"].append(feat.properties.heartrate)
        extensions["cadence"].append(feat.properties.cadence)
        extensions["power"].append(feat.properties.power)
        extensions["temperature"].append(feat.properties.temperature)

    track = PyTrack(
        points=points,
        elevations=None if allow_empty_spatial else elevations,
        times=times,
        extensions=extensions,  # type: ignore
    )

    return track


def _convert_linestrings_collection(
    data: dict, allow_empty_spatial: bool, fallback_coordinates: tuple[float, float]
) -> Track:
    _data = LineFeature.model_validate(data)

    if not allow_empty_spatial and _data.geometry is None:
        raise ValueError("Geometry is missing")

    _times = _data.properties.times
    if allow_empty_spatial:
        _corrdinates = None
    else:
        assert _data.geometry is not None
        _corrdinates = _data.geometry.coordinates
    _heartrates = _data.properties.heartrates
    _cadences = _data.properties.cadences
    _powers = _data.properties.powers
    _temperatures = _data.properties.temperatures

    if _corrdinates is not None and len(_corrdinates) != len(_times):
        raise ValueError("Number of coordinates does not match number of timestamps")
    if _heartrates and len(_times) != len(_heartrates):
        raise ValueError("Number of coordinates does not match number of heartrates")
    if _cadences and len(_times) != len(_cadences):
        raise ValueError("Number of coordinates does not match number of cadences")
    if _powers and len(_times) != len(_powers):
        raise ValueError("Number of coordinates does not match number of powers")
    if _temperatures and len(_times) != len(_temperatures):
        raise ValueError("Number of coordinates does not match number of temperatures")

    points = []
    elevations = []
    if _corrdinates:
        for coord in _corrdinates:
            lon, lat, ele = coord
            points.append((lat, lon))
            elevations.append(ele)
    else:
        elevations = None
        points = [fallback_coordinates] * len(_times)

    track = PyTrack(
        points=points,
        elevations=elevations,
        times=_times,
        extensions=dict(
            heartrate=_heartrates,
            power=_powers,
            cadence=_cadences,
            temperature=_temperatures,
        ),  # type: ignore
    )

    return track


def read_raw_data(
    data: dict, allow_empty_spatial: bool, fallback_coordinates: tuple[float, float]
) -> Track:
    format = "unknown"
    if data.get("type") == "FeatureCollection":
        format = "points_collection"
    elif data.get("type") == "Feature":
        format = "linestrings_collection"
    else:
        # TODO: Better error message that reference the documentation
        raise ValueError("Unsupported GeoJSON format")

    if format == "points_collection":
        return _convert_points_collection(
            data=data,
            allow_empty_spatial=allow_empty_spatial,
            fallback_coordinates=fallback_coordinates,
        )
    elif format == "linestrings_collection":
        return _convert_linestrings_collection(
            data=data,
            allow_empty_spatial=allow_empty_spatial,
            fallback_coordinates=fallback_coordinates,
        )
    else:
        raise ValueError("Unsupported GeoJSON format")

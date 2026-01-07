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
    geometry: PointGeometry
    properties: PointProperties


class LineFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: LineStringGeometry
    properties: LineProperties


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[PointFeature]
    properties: BaseProperties | None = None


def _convert_points_collection(data: dict, allow_empty_spatial: bool) -> Track:
    _data = FeatureCollection.model_validate(data)

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
        elevations=elevations,
        times=times,
        extensions=extensions,  # type: ignore
    )

    return track


def _convert_linestrings_collection(data: dict, allow_empty_spatial: bool) -> Track:
    _data = LineFeature.model_validate(data)
    _corrdinates = _data.geometry.coordinates
    _times = _data.properties.times
    _heartrates = _data.properties.heartrates
    _cadences = _data.properties.cadences
    _powers = _data.properties.powers
    _temperatures = _data.properties.temperatures

    if len(_corrdinates) != len(_times):
        raise ValueError("Number of coordinates does not match number of timestamps")
    if _heartrates and len(_corrdinates) != len(_heartrates):
        raise ValueError("Number of coordinates does not match number of heartrates")
    if _cadences and len(_corrdinates) != len(_cadences):
        raise ValueError("Number of coordinates does not match number of cadences")
    if _powers and len(_corrdinates) != len(_powers):
        raise ValueError("Number of coordinates does not match number of powers")
    if _temperatures and len(_corrdinates) != len(_temperatures):
        raise ValueError("Number of coordinates does not match number of temperatures")

    points = []
    elevations = []
    for coord in _corrdinates:
        lon, lat, ele = coord
        points.append((lat, lon))
        elevations.append(ele)

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


def read_raw_data(data: dict, allow_empty_spatial: bool) -> Track:
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
            data=data, allow_empty_spatial=allow_empty_spatial
        )
    elif format == "linestrings_collection":
        return _convert_linestrings_collection(
            data=data, allow_empty_spatial=allow_empty_spatial
        )
    else:
        raise ValueError("Unsupported GeoJSON format")

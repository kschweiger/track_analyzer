from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from geo_track_analyzer import PyTrack, Track
from geo_track_analyzer.exceptions import (
    EmptyGeoJsonError,
    GeoJsonWithoutGeometryError,
    UnsupportedGeoJsonTypeError,
)

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


class PointCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[PointFeature]
    properties: BaseProperties | None = None


class LineCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[LineFeature]
    properties: BaseProperties | None = None


def _convert_points_collection(
    data: dict, allow_empty_spatial: bool, fallback_coordinates: tuple[float, float]
) -> Track:
    _data = PointCollection.model_validate(data)

    if not allow_empty_spatial and any(g.geometry is None for g in _data.features):
        raise GeoJsonWithoutGeometryError("One or more features have no geometry")

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


def _cast_line_feature_to_data(
    data: LineFeature,
    allow_empty_spatial: bool,
    fallback_coordinates: tuple[float, float],
) -> tuple[
    list[tuple[float, float]], list[float] | None, list[datetime], dict[str, list]
]:
    if not allow_empty_spatial and data.geometry is None:
        raise GeoJsonWithoutGeometryError("Geometry is missing")

    if not allow_empty_spatial and data.geometry is None:
        raise GeoJsonWithoutGeometryError("Geometry is missing")

    _times = data.properties.times
    if allow_empty_spatial:
        _corrdinates = None
    else:
        assert data.geometry is not None
        _corrdinates = data.geometry.coordinates
    _heartrates = data.properties.heartrates
    _cadences = data.properties.cadences
    _powers = data.properties.powers
    _temperatures = data.properties.temperatures

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

    return (
        points,
        elevations,
        _times,
        dict(
            heartrate=_heartrates,
            power=_powers,
            cadence=_cadences,
            temperature=_temperatures,
        ),  # type: ignore
    )


def _convert_linestrings_collection(
    data: dict, allow_empty_spatial: bool, fallback_coordinates: tuple[float, float]
) -> Track:
    _data = LineFeature.model_validate(data)

    points, elevations, times, extensions = _cast_line_feature_to_data(
        _data, allow_empty_spatial, fallback_coordinates
    )

    track = PyTrack(
        points=points,
        elevations=elevations,
        times=times,
        extensions=extensions,  # type: ignore
    )

    return track


def _convert_linestrings_multisegment_collection(
    data: dict, allow_empty_spatial: bool, fallback_coordinates: tuple[float, float]
) -> Track:
    _data = LineCollection.model_validate(data)

    if len(_data.features) == 0:
        raise EmptyGeoJsonError("No features in GeoJSON data")

    features_iter = iter(_data.features)

    # Initialize with first segment
    first_segment = next(features_iter)
    points, elevations, times, extensions = _cast_line_feature_to_data(
        first_segment, allow_empty_spatial, fallback_coordinates
    )
    track = PyTrack(
        points=points,
        elevations=elevations,
        times=times,
        extensions=extensions,  # type: ignore
    )

    # Add remaining segments
    for segment in features_iter:
        points, elevations, times, extensions = _cast_line_feature_to_data(
            segment, allow_empty_spatial, fallback_coordinates
        )
        track.add_segmeent(
            points=points,
            elevations=elevations,
            times=times,
            extensions=extensions,  # type: ignore
        )

    return track


def read_raw_data(
    data: dict, allow_empty_spatial: bool, fallback_coordinates: tuple[float, float]
) -> Track:
    format = None
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
        if features:
            properties = features[0].get("properties", {})
            if properties.get("coordTimes") is not None:
                format = "linestrings_multisegment_collection"
            else:
                format = "points_collection"
    elif data.get("type") == "Feature":
        format = "linestrings_collection"
    if format is None:
        raise UnsupportedGeoJsonTypeError("Unsupported GeoJSON format")

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
    elif format == "linestrings_multisegment_collection":
        return _convert_linestrings_multisegment_collection(
            data=data,
            allow_empty_spatial=allow_empty_spatial,
            fallback_coordinates=fallback_coordinates,
        )
    else:
        raise ValueError("Unsupported GeoJSON format")

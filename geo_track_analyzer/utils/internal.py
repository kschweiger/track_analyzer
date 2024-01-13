from datetime import datetime
from typing import Any, Callable, ClassVar, Dict, Union
from xml.etree.ElementTree import Element

from gpxpy.gpx import GPXTrackPoint
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from geo_track_analyzer.exceptions import GPXPointExtensionError


class ExtensionFieldElement(Element):
    def __init__(self, name: str, text: str) -> None:
        super().__init__(name)
        self.text = text


def get_extended_track_point(
    lat: float,
    lng: float,
    ele: None | float,
    timestamp: None | datetime,
    extensions: Dict[str, Union[str, float, int]],
) -> GPXTrackPoint:
    """
    Create a GPXTrackPoint with extended data fields.

    :param lat: Latitude of the track point.
    :param lng: Longitude of the track point.
    :param ele: Elevation of the track point (None if not available).
    :param timestamp: Timestamp of the track point (None if not available).
    :param extensions: Dictionary of extended data fields (key-value pairs).

    :return: GPXTrackPoint with specified attributes and extended data fields.
    """
    this_point = GPXTrackPoint(lat, lng, elevation=ele, time=timestamp)
    for key, value in extensions.items():
        this_point.extensions.append(ExtensionFieldElement(name=key, text=str(value)))

    return this_point


def get_extension_value(point: GPXTrackPoint, key: str) -> str:
    for ext in point.extensions:
        if ext.tag == key:
            if ext.text is None:
                GPXPointExtensionError("Key %s was not initilized with a value" % key)
            return ext.text  # type: ignore

    raise GPXPointExtensionError("Key %s could not be found" % key)


class GPXTrackPointAfterValidator:
    valid_float_params: ClassVar[list[str]] = [
        "latitude",
        "longitude",
        "elevation",
        "horizontal_dilution",
        "vertical_dilution",
        "position_dilution",
        "speed",
        "heartrate",
        "cadence",
        "power",
    ]
    valid_str_params: ClassVar[list[str]] = [
        "symbol",
        "comment",
        "name",
    ]
    valid_dt_params: ClassVar[list[str]] = ["time"]

    extensions: ClassVar[list[str]] = [
        "heartrate",
        "cadence",
        "power",
    ]
    extensions_type_map: ClassVar[dict[str, Callable[[str], Any]]] = {
        "heartrate": float,
        "cadence": float,
        "power": float,
    }

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler  # noqa: ANN401
    ) -> CoreSchema:
        def validate_from_dict(value: dict[str, Any]) -> GPXTrackPoint:
            conv_dict: dict[str, Any] = {}
            for key, val in value.items():
                if key in cls.valid_float_params:
                    conv_dict[key] = float(val)
                elif key in cls.valid_str_params:
                    conv_dict[key] = str(val)
                elif key in cls.valid_dt_params:
                    try:
                        conv_dict[key] = datetime.fromisoformat(val)
                    except TypeError:
                        raise ValueError(
                            f"Value for {key} must valid isoformatted string"
                        )
                else:
                    raise ValueError(f"{key} is no valid parameter for GPXTrackPoint")

            pnt = GPXTrackPoint(
                **{k: v for k, v in conv_dict.items() if k not in cls.extensions}
            )
            for key, val in {
                k: v for k, v in conv_dict.items() if k in cls.extensions
            }.items():
                pnt.extensions.append(ExtensionFieldElement(name=key, text=str(val)))

            return pnt

        def dump_to_dict(
            point: GPXTrackPoint,
            supported_keys: list[str],
            extensions: list[str],
            extensions_type_map: dict[str, Callable[[str], Any]],
        ) -> dict[str, Any]:
            dump_dict = {}
            for key in supported_keys:
                if key in extensions:
                    continue
                val = getattr(point, key)
                if val:  # Ignore None and empty lists
                    dump_dict[key] = val

            if point.extensions:
                for ext in extensions:
                    try:
                        val = get_extension_value(point, ext)
                    except GPXPointExtensionError:
                        pass
                    else:
                        dump_dict[ext] = extensions_type_map[ext](val)

            return dump_dict

        from_dict_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(),
                core_schema.no_info_plain_validator_function(validate_from_dict),
            ]
        )

        keys_supported = (
            cls.valid_dt_params + cls.valid_str_params + cls.valid_float_params
        )

        return core_schema.json_or_python_schema(
            json_schema=from_dict_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(GPXTrackPoint), from_dict_schema]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: dump_to_dict(
                    instance, keys_supported, cls.extensions, cls.extensions_type_map
                )
            ),
        )

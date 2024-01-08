"""
Enhance gpx tracks with external data. E.g. elevation data
"""
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Mapping, Type, final

import requests
from gpxpy.gpx import GPXTrack
from requests.structures import CaseInsensitiveDict

from geo_track_analyzer.exceptions import (
    APIDataNotAvailableError,
    APIHealthCheckFailedError,
    APIResponseError,
)

logger = logging.getLogger(__name__)


class EnhancerType(str, Enum):
    OPENTOPOELEVATION = "OpenTopoElevation"
    OPENELEVATION = "OpenElevation"


class Enhancer(ABC):
    """Base class for GPX Track enhancement"""

    @abstractmethod
    def __init__(self, url: str) -> None:
        pass

    @abstractmethod
    def enhance_track(self, track: GPXTrack, inplace: bool = False) -> GPXTrack:
        pass


class ElevationEnhancer(Enhancer):
    """Base class for enhancing GPX Tracks with externally provided elevation data"""

    def enhance_track(self, track: GPXTrack, inplace: bool = False) -> GPXTrack:
        """
        Main method to enhance a passed GPX track with elevation information

        :param track: Track to be enhanced.

        :returns: The enhanced track
        """
        if inplace:
            track_ = track
        else:
            track_ = track.clone()

        for segment in track_.segments:
            request_coordinates = []
            for point in segment.points:
                request_coordinates.append((point.latitude, point.longitude))

            elevations = self.get_elevation_data(request_coordinates)
            for point, elevation in zip(segment.points, elevations):
                point.elevation = elevation

        return track_

    @abstractmethod
    def get_elevation_data(
        self, input_coordinates: list[tuple[float, float]]
    ) -> list[float]:
        pass


@final
class OpenTopoElevationEnhancer(ElevationEnhancer):
    """Use the/a OpenTopoData API (https://opentopodata.org) to enhance a GPX track
    with elevation information."""

    def __init__(
        self,
        url: str = "https://api.opentopodata.org/",
        dataset: str = "eudem25m",
        interpolation: str = "cubic",
        skip_checks: bool = False,
    ) -> None:
        """
        Setup the enhancer via a opentopodata rest api.

        :param url: REST api entrypoint url, defaults to "https://api.opentopodata.org/"
        :param dataset: Dataset of elevation data , defaults to "eudem25m"
        :param interpolation: Interpolation method, defaults to "cubic"
        :param skip_checks: If true, health checks will be skipped on initialization,
            defaults to False
        :raises APIHealthCheckFailedError: If connection can not established
        :raises APIHealthCheckFailedError: Any other error on health check
        :raises APIDataNotAvailableError: Dataset is not available at the endpoint
        """
        self.base_url = url
        self.url = f"{url}/v1/{dataset}"
        self.interpolation = interpolation

        if not skip_checks:
            logger.debug("Doing server health check")
            try:
                resp = requests.get(f"{self.base_url}/health")
            except requests.exceptions.ConnectionError as e:
                raise APIHealthCheckFailedError(str(e))
            if resp.status_code != 200:
                raise APIHealthCheckFailedError(resp.text)

            logger.debug("Doing dataset check")
            resp = requests.get(f"{self.base_url}/datasets")
            if resp.status_code != 200:
                raise APIHealthCheckFailedError(resp.text)
            datasets = [ds["name"] for ds in resp.json()["results"]]
            if dataset not in datasets:
                raise APIDataNotAvailableError("Dataset %s not available" % dataset)

    def get_elevation_data(
        self,
        input_coordinates: list[tuple[float, float]],
        split_requests: None | int = None,
    ) -> list[float]:
        """Send a post request to the api endoint to query elevation data
        for the passed input coordinates

        :param input_coordinates: list of latitude, longitude tuples for which the
            elevation should be determined.

        :param split_requests: Optionally split request into multiple requires to get
            around size restrictions, defaults to None
        :raises APIResponseError: Any none 200 response form the endpoint

        :returns: A list of Elevations for the passed coordinates.
        """
        logger.debug("Getting elevation data")
        if split_requests is None:
            split_input_coord = [input_coordinates]
        else:
            split_input_coord = [
                input_coordinates[i : i + split_requests]
                for i in range(0, len(input_coordinates), split_requests)
            ]

        ret_elevations = []
        for coords in split_input_coord:
            locations = ""
            for latitude, longitude in coords:
                locations += f"{latitude},{longitude}|"

            locations = locations[:-1]
            resp = requests.post(
                self.url,
                data={
                    "locations": locations,
                    "interpolation": self.interpolation,
                },
            )

            if resp.status_code == 200:
                result_data = resp.json()
                for res in result_data["results"]:
                    ret_elevations.append(res["elevation"])

            else:
                raise APIResponseError(resp.text)

        return ret_elevations


@final
class OpenElevationEnhancer(ElevationEnhancer):
    """Use the/a OpenElevation API (https://open-elevation.com) to enhance a GPX track
    with elevation information."""

    def __init__(self, url: str = "https://api.open-elevation.com") -> None:
        """
        Setup the enhancer via the url of the rest api of open-elevation

        :param url: URL of the API gateway
        """
        self.url = f"{url}/api/v1/lookup"

        self.headers: Mapping[str, str] = CaseInsensitiveDict()
        self.headers["Accept"] = "application/json"
        self.headers["Content-Type"] = "application/json"

    def get_elevation_data(
        self, input_coordinates: list[tuple[float, float]]
    ) -> list[float]:
        """
        Send a POST request to the Open-Elevation API specified in the init.

        :param input_coordinates: list of latitude, longitude tuples for which the
            elevation should be determined.

        :returns: A list of Elevations for the passed coordinates.
        """
        data: Dict = {"locations": []}
        for latitude, longitude in input_coordinates:
            data["locations"].append({"latitude": latitude, "longitude": longitude})

        resp = requests.post(self.url, headers=self.headers, data=json.dumps(data))

        if resp.status_code == 200:
            result_data = resp.json()
            ret_elevations = []
            for res in result_data["results"]:
                ret_elevations.append(float(res["elevation"]))

            return ret_elevations
        else:
            raise APIResponseError(resp.text)


def get_enhancer(name: EnhancerType) -> Type[Enhancer]:
    """Get a Enhance object for a specific enpoint by passing a distinct name

    :param name: Name of enhancer. Chose OpenTopoElevation or OpenElevation
    :raises NotImplementedError: If an invalid name is passed
    :return: An Enhancer object
    """
    if name == EnhancerType.OPENTOPOELEVATION:
        return OpenTopoElevationEnhancer
    elif name == EnhancerType.OPENELEVATION:
        return OpenElevationEnhancer
    else:
        raise NotImplementedError("Can not return Enhancer for name %s" % name)

"""
Enhance gpx tracks with external data. E.g. elevation data
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import requests
from gpxpy.gpx import GPXTrack
from requests.structures import CaseInsensitiveDict

from gpx_track_analyzer.exceptions import (
    APIDataNotAvailableException,
    APIHealthCheckFailedException,
    APIResponseException,
)

logger = logging.getLogger(__name__)


class Enhancer(ABC):
    """Base class for GPX Track enhancement"""

    @abstractmethod
    def enhance_track(self, track: GPXTrack, inplace: bool = False) -> GPXTrack:
        pass


class ElevationEnhancer(Enhancer):
    """Base class for enhancing GPX Tracks with externally provided elevation data"""

    def enhance_track(self, track: GPXTrack, inplace: bool = False) -> GPXTrack:
        """
        Main method to enhance a passed GPX track with elevation information

        Args:
            track: Track to be enhanced.

        Returns: The enhanced track

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
        self, input_coordinates: List[Tuple[float, float]]
    ) -> List[float]:
        pass


class OpenTopoElevationEnhancer(ElevationEnhancer):
    def __init__(
        self,
        url="https://api.opentopodata.org/",
        dataset="eudem25m",
        interpolation="cubic",
        skip_checks: bool = False,
    ):
        self.base_url = url
        self.url = f"{url}/v1/{dataset}"
        self.interpolation = interpolation

        if not skip_checks:
            logger.debug("Doing server health check")
            try:
                resp = requests.get(f"{self.base_url}/health")
            except requests.exceptions.ConnectionError as e:
                raise APIHealthCheckFailedException(str(e))
            if resp.status_code != 200:
                raise APIHealthCheckFailedException(resp.text)

            logger.debug("Doing dataset check")
            resp = requests.get(f"{self.base_url}/datasets")
            if resp.status_code != 200:
                raise APIHealthCheckFailedException(resp.text)
            datasets = [ds["name"] for ds in resp.json()["results"]]
            if dataset not in datasets:
                raise APIDataNotAvailableException("Dataset %s not available" % dataset)

    def get_elevation_data(
        self,
        input_coordinates: List[Tuple[float, float]],
        split_requests: Optional[int] = None,
    ) -> List[float]:
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
                raise APIResponseException(resp.text)

        return ret_elevations


class OpenElevationEnhancer(ElevationEnhancer):
    def __init__(self, url="https://api.open-elevation.com"):
        """
        Use the/a OpenElevation API (https://open-elevation.com) to enhance a GPX track
        with elevation information. Alternatively, set up you own open-elevation api
        and set the url accordingly.

        Default points
        Args:
            url: URL of the API gateway
        """
        self.url = f"{url}/api/v1/lookup"

        self.headers = CaseInsensitiveDict()
        self.headers["Accept"] = "application/json"
        self.headers["Content-Type"] = "application/json"

    def get_elevation_data(
        self, input_coordinates: List[Tuple[float, float]]
    ) -> List[float]:
        """
        Send a POST request to the Open-Elevation API specified in the init.

        Args:
            input_coordinates: List of latitude, longitude tuples for which the
                               elevation should be determined.

        Returns: A List of Elevations for the passed coordinates.
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
            raise APIResponseException(resp.text)


def get_enhancer(name: str) -> Enhancer:
    if name == "OpenTopoElevation":
        return OpenTopoElevationEnhancer
    elif name == "OpenElevation":
        return OpenElevationEnhancer
    else:
        raise NotImplementedError("Can not return Enhancer for name %s" % name)

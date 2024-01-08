import os
from time import sleep
from typing import Type

import gpxpy
import pytest
from gpxpy.gpx import GPXTrack
from pytest_mock import MockerFixture

from geo_track_analyzer.enhancer import (
    EnhancerType,
    OpenElevationEnhancer,
    OpenTopoElevationEnhancer,
    get_enhancer,
)
from geo_track_analyzer.exceptions import APIResponseError


@pytest.mark.skip("Currently not working. Also not the best option out there... ")
def test_open_elevation_enhancer() -> None:
    enhancer = OpenElevationEnhancer()

    query_data = [(10, 10), (20, 20), (41.161758, -8.583933)]

    ret_data = enhancer.get_elevation_data(query_data)

    assert ret_data == [515, 545, 117]


@pytest.mark.skip("Currently not working. Also not the best option out there... ")
def test_open_elevation_enhancer_api_exceptions() -> None:
    enhancer = OpenElevationEnhancer()

    with pytest.raises(APIResponseError):
        enhancer.get_elevation_data([])


@pytest.mark.dependency()
def test_opentopo_elevation_enhancer() -> None:
    sleep(2)
    enhancer = OpenTopoElevationEnhancer()

    query_data = [(48.8588897, 2.320041), (41.161758, -8.583933)]

    ret_data = enhancer.get_elevation_data(query_data)

    assert ret_data == [44.59263610839844, 113.41450500488281]


@pytest.mark.dependency(depends=["test_opentopo_elevation_enhancer"])
@pytest.mark.skipif(os.environ.get("TEST_ENV") == "CI", reason="Not tested on CI")
def test_opentopo_elevation_enhancer_splitting() -> None:
    sleep(5)
    enhancer = OpenTopoElevationEnhancer()

    query_data = [(48.8588897, 2.320041), (41.161758, -8.583933)]

    ret_data = enhancer.get_elevation_data(query_data, 1)

    assert ret_data == [44.59263610839844, 113.41450500488281]


def enhancer_test_track(
    mocker: MockerFixture, inplace: bool
) -> tuple[GPXTrack, GPXTrack]:
    enhancer = OpenTopoElevationEnhancer(skip_checks=True)

    mock_get_data = mocker.Mock()
    mock_get_data.return_value = [250, 275]
    enhancer.get_elevation_data = mock_get_data

    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for lat, long, ele in [(1, 1, 100), (2, 2, 100)]:
        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                lat,
                long,
                elevation=ele,
            )
        )

    return gpx_track, enhancer.enhance_track(gpx_track, inplace=inplace)


def test_enhancer_enhance_track(mocker: MockerFixture) -> None:
    orig_track, enhanced_track = enhancer_test_track(mocker, False)

    assert orig_track != enhanced_track

    assert orig_track.segments[0].points[0].elevation == 100
    assert orig_track.segments[0].points[1].elevation == 100

    assert enhanced_track.segments[0].points[0].elevation == 250
    assert enhanced_track.segments[0].points[1].elevation == 275


def test_enhancer_enhance_track_inplace(mocker: MockerFixture) -> None:
    orig_track, enhanced_track = enhancer_test_track(mocker, True)

    assert orig_track == enhanced_track

    assert orig_track.segments[0].points[0].elevation != 100
    assert orig_track.segments[0].points[1].elevation != 100

    assert orig_track.segments[0].points[0].elevation == 250
    assert orig_track.segments[0].points[1].elevation == 275

    assert enhanced_track.segments[0].points[0].elevation == 250
    assert enhanced_track.segments[0].points[1].elevation == 275


@pytest.mark.parametrize(
    ("in_arg", "ret_type"),
    [
        (EnhancerType.OPENELEVATION, OpenElevationEnhancer),
        (EnhancerType.OPENTOPOELEVATION, OpenTopoElevationEnhancer),
        ("OpenElevation", OpenElevationEnhancer),
        ("OpenTopoElevation", OpenTopoElevationEnhancer),
    ],
)
def test_get_enhancer(in_arg: EnhancerType | str, ret_type: Type) -> None:
    assert get_enhancer(in_arg) == ret_type

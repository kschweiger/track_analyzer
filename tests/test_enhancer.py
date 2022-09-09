import os

import pytest

from gpx_track_analyzer.enhancer import OpenElevationEnhancer, OpenTopoElevationEnhancer
from gpx_track_analyzer.exceptions import APIResponseExceptions


@pytest.mark.skip("Currently not working. Also not the best option out there... ")
def test_open_elevation_enhancer():
    enhancer = OpenElevationEnhancer()

    query_data = [(10, 10), (20, 20), (41.161758, -8.583933)]

    ret_data = enhancer.get_elevation_data(query_data)

    assert ret_data == [515, 545, 117]


@pytest.mark.skip("Currently not working. Also not the best option out there... ")
def test_open_elevation_enhancer_api_exceptions():
    enhancer = OpenElevationEnhancer()

    with pytest.raises(APIResponseExceptions):
        enhancer.get_elevation_data([])


def test_opentopo_elevation_enhancer():
    enhancer = OpenTopoElevationEnhancer()

    query_data = [(48.8588897, 2.320041), (41.161758, -8.583933)]

    ret_data = enhancer.get_elevation_data(query_data)

    assert ret_data == [44.59263610839844, 113.41450500488281]


@pytest.mark.skipif(os.environ.get("TEST_ENV") == "CI", reason="Not tested on CI")
def test_opentopo_elevation_enhancer_splitting():
    enhancer = OpenTopoElevationEnhancer()

    query_data = [(48.8588897, 2.320041), (41.161758, -8.583933)]

    ret_data = enhancer.get_elevation_data(query_data, 1)

    assert ret_data == [44.59263610839844, 113.41450500488281]

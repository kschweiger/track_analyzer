import pytest

from gpx_track_analyzer.enhancer import OpenElevationEnhancer
from gpx_track_analyzer.exceptions import APIResponseExceptions


def test_open_elevation_enhancer():
    enhancer = OpenElevationEnhancer()

    query_data = [(10, 10), (20, 20), (41.161758, -8.583933)]

    ret_data = enhancer.get_elevation_data(query_data)

    assert ret_data == [515, 545, 117]


def test_open_elevation_enhancer_api_exceptions():
    enhancer = OpenElevationEnhancer()

    with pytest.raises(APIResponseExceptions):
        enhancer.get_elevation_data([])

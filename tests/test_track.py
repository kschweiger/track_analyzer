import importlib.resources
from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest
from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint, GPXTrackSegment
from plotly.graph_objs.graph_objs import Figure
from pytest_mock import MockerFixture

from geo_track_analyzer.exceptions import (
    TrackInitializationError,
    TrackTransformationError,
    VisualizationSetupError,
)
from geo_track_analyzer.model import SegmentOverview, ZoneInterval, Zones
from geo_track_analyzer.track import ByteTrack, GPXFileTrack, PyTrack, Track
from geo_track_analyzer.utils.internal import get_extension_value
from tests import resources


@pytest.fixture()
def two_segment_py_data() -> tuple[tuple[list, list, list], tuple[list, list, list]]:
    segment_1_points = [
        (46.74025, 11.95624),
        (46.74027, 11.95587),
        (46.74013, 11.95575),
        (46.73946, 11.95588),
        (46.73904, 11.95627),
        (46.73852, 11.95609),
    ]
    segment_1_elevations = [2248, 2247, 2244, 2245, 2252, 2256]
    segment_1_times = [
        datetime(2023, 8, 1, 10),
        datetime(2023, 8, 1, 10, 1),
        datetime(2023, 8, 1, 10, 2),
        datetime(2023, 8, 1, 10, 3),
        datetime(2023, 8, 1, 10, 4),
        datetime(2023, 8, 1, 10, 5),
    ]
    ####
    segment_2_points = [
        (46.73861, 11.95697),
        (46.73862, 11.95755),
        (46.73878, 11.95778),
        (46.73910, 11.95763),
        (46.73930, 11.95715),
        (46.74021, 11.95627),
    ]

    segment_2_elevations = [2263, 2268, 2270, 2269, 2266, 2248]
    segment_2_times = [
        datetime(2023, 8, 1, 10, 6),
        datetime(2023, 8, 1, 10, 7),
        datetime(2023, 8, 1, 10, 8),
        datetime(2023, 8, 1, 10, 9),
        datetime(2023, 8, 1, 10, 9),
        datetime(2023, 8, 1, 10, 10),
    ]

    return (segment_1_points, segment_1_elevations, segment_1_times), (
        segment_2_points,
        segment_2_elevations,
        segment_2_times,
    )


@pytest.fixture()
def generate_mock_track() -> GPX:
    gpx = GPX()

    # Create first track in our GPX:
    gpx_track = GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Create points:
    point_values = [
        (2.1234, 5, 100, "2022-06-01T14:30:35+00:00"),
        (2.1235, 5, 105, "2022-06-01T14:30:40+00:00"),
        (2.1236, 5, 110, "2022-06-01T14:30:45+00:00"),
        (2.1237, 5, 115, "2022-06-01T14:30:50+00:00"),
        (2.1238, 5, 105, "2022-06-01T14:30:55+00:00"),
        (2.1239, 5, 100, "2022-06-01T14:31:00+00:00"),
        (2.1240, 5, 90, "2022-06-01T14:31:05+00:00"),
        (2.1241, 5, 100, "2022-06-01T14:31:10+00:00"),
    ]

    for lat, long, ele, isotime in point_values:
        gpx_segment.points.append(
            GPXTrackPoint(
                lat,
                long,
                elevation=ele,
                time=datetime.fromisoformat(isotime),
            )
        )

    return gpx


def test_track(generate_mock_track: GPX) -> None:
    MockedFileTrack = GPXFileTrack  # noqa: N806
    MockedFileTrack._get_gpx = MagicMock()
    MockedFileTrack._get_gpx.return_value = generate_mock_track

    track = MockedFileTrack("bogus_file_name.gpx")
    segment_overview = track.get_segment_overview(0)
    assert isinstance(segment_overview, SegmentOverview)


@pytest.mark.parametrize(
    ("points", "elevations", "time"),
    [
        ([(50, 50), (51, 51), (52, 52)], None, None),
        ([(50, 50), (51, 51), (52, 52)], [100, 200, 300], None),
        (
            [(50, 50), (51, 51), (52, 52)],
            None,
            [
                datetime(2023, 1, 1, 10),
                datetime(2023, 1, 1, 11),
                datetime(2023, 1, 1, 12),
            ],
        ),
        (
            [(50, 50), (51, 51), (52, 52)],
            [100, 200, 300],
            [
                datetime(2023, 1, 1, 10),
                datetime(2023, 1, 1, 11),
                datetime(2023, 1, 1, 12),
            ],
        ),
    ],
)
def test_py_track(
    points: list[tuple[float, float]],
    elevations: None | list[float],
    time: None | list[datetime],
) -> None:
    track = PyTrack(points, elevations, time)

    assert isinstance(track.track, GPXTrack)

    data = track.get_segment_data()

    assert isinstance(data, pd.DataFrame)

    overview = track.get_segment_overview()

    assert isinstance(overview, SegmentOverview)


@pytest.mark.parametrize(
    ("points", "elevations", "time"),
    [
        ([(50, 50), (51, 51), (52, 52)], [100, 200], None),
        (
            [(50, 50), (51, 51), (52, 52)],
            None,
            [
                datetime(2023, 1, 1, 10),
                datetime(2023, 1, 1, 11),
            ],
        ),
    ],
)
def test_py_track_init_exceptions(
    points: list[tuple[float, float]],
    elevations: None | list[float],
    time: None | list[datetime],
) -> None:
    with pytest.raises(TrackInitializationError):
        PyTrack(points, elevations, time)


def test_interpolate_linear_points_in_segment_lat_lng_only() -> None:
    # Distacne 2d: ~1000m
    track = PyTrack([(0, 0), (0.0089933, 0)], None, None)

    track.interpolate_points_in_segment(spacing=200)

    assert len(track.track.segments[0].points) == 6
    for point in track.track.segments[0].points:
        assert point.elevation is None
        assert point.time is None


def test_interpolate_linear_points_in_segment_no_interpolation() -> None:
    track = PyTrack([(0, 0), (0.0089933, 0)], None, None)

    track.interpolate_points_in_segment(spacing=2000)

    assert len(track.track.segments[0].points) == 2


def test_interpolate_linear_points_in_segment_lat_lng_ele() -> None:
    track = PyTrack([(0, 0), (0.0089933, 0)], [100, 200], None)

    track.interpolate_points_in_segment(spacing=200)

    assert len(track.track.segments[0].points) == 6
    for point in track.track.segments[0].points:
        assert point.elevation is not None
        assert point.time is None


def test_interpolate_linear_points_in_segment_lat_lng_ele_time() -> None:
    # Distacne 2d: ~1000m
    track = PyTrack(
        [(0, 0), (0.0089933, 0)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    track.interpolate_points_in_segment(spacing=200)

    assert len(track.track.segments[0].points) == 6
    for point in track.track.segments[0].points:
        assert point.elevation is not None
        assert point.time is not None


@pytest.mark.parametrize(
    ("points", "n_exp"),
    [
        ([(0, 0), (0.0089933, 0), (0.0010, 0)], 10),
        ([(0, 0), (0.0089933, 0), (0.0010, 0), (0.0011, 0)], 11),
    ],
)
def test_interpolate_linear_points_in_segment_multiple_points(
    points: list[tuple[float, float]], n_exp: int
) -> None:
    # Distacne 2d: ~1000m
    track = PyTrack(points, None, None)

    track.interpolate_points_in_segment(spacing=200)

    assert len(track.track.segments[0].points) == n_exp


@pytest.mark.parametrize(
    ("coords", "eles", "times"),
    [
        ([(1, 1), (2, 2)], None, None),
        ([(1, 1), (2, 2)], [100, 200], None),
        (
            [(1, 1), (2, 2)],
            [100, 200],
            [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
        ),
    ],
)
def test_get_point_data_in_segmnet(
    coords: list[tuple[float, float]],
    eles: None | list[float],
    times: None | list[datetime],
) -> None:
    track = PyTrack(coords, eles, times)

    ret_coords, ret_eles, ret_times = track.get_point_data_in_segmnet(0)

    assert ret_coords == coords
    assert ret_eles == eles
    assert ret_times == times


def test_get_point_data_in_segment_exception_ele() -> None:
    track = PyTrack(
        [(1, 1), (2, 2)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    track.track.segments[0].points[1].elevation = None

    with pytest.raises(TrackTransformationError):
        track.get_point_data_in_segmnet()


def test_get_point_data_in_segment_exception_time() -> None:
    track = PyTrack(
        [(1, 1), (2, 2)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    track.track.segments[0].points[1].time = None

    with pytest.raises(TrackTransformationError):
        track.get_point_data_in_segmnet()


def test_get_closest_point() -> None:
    track = PyTrack(
        [(1, 1), (2, 2)],
        [100, 200],
        [datetime(2023, 1, 1, 10), datetime(2023, 1, 1, 10, 30)],
    )

    distance_result = track.get_closest_point(0, 1.1, 1.1)

    point, distance, idx = (
        distance_result.point,
        distance_result.distance,
        distance_result.segment_point_idx,
    )

    assert isinstance(point, GPXTrackPoint)
    assert isinstance(distance, float)
    assert isinstance(idx, int)

    assert idx == 0
    assert point.latitude == 1
    assert point.longitude == 1
    assert point.elevation == 100
    assert point.time == datetime(2023, 1, 1, 10, 0)


def test_overlap() -> None:
    resource_files = importlib.resources.files(resources)

    track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes()
    )

    match_track = ByteTrack(
        (resource_files / "Teilstueck_Schau_ins_land.gpx").read_bytes()
    )

    overlap_tracks = track.find_overlap_with_segment(0, match_track)

    assert len(overlap_tracks) == 1

    overlap_track, overlap_frac, inverse = overlap_tracks[0]

    assert isinstance(overlap_track, Track)
    assert overlap_frac == 1.0
    assert not inverse


def test_pytrack_extensions() -> None:
    track = PyTrack(
        [(1, 1)],
        [100],
        [datetime(2023, 1, 1, 10)],
        heartrate=[100],
        cadence=[80],
        power=[200],
    )

    point = track.track.segments[0].points[0]

    assert get_extension_value(point, "heartrate") == "100"
    assert get_extension_value(point, "cadence") == "80"
    assert get_extension_value(point, "power") == "200"


def test_pytrack_add_segement() -> None:
    track = PyTrack(
        [(1, 1)],
        [100],
        [datetime(2023, 1, 1, 10)],
        heartrate=[100],
        cadence=[80],
        power=[200],
    )

    assert len(track.track.segments) == 1

    track.add_segmeent(
        [(2, 2)],
        [200],
        [datetime(2023, 2, 1, 10)],
        heartrate=[60],
        cadence=[20],
        power=[100],
    )

    assert len(track.track.segments) == 2


def test_track_overiew(
    two_segment_py_data: tuple[tuple[list, list, list], tuple[list, list, list]],
) -> None:
    (
        (segment_1_points, segment_1_elevations, segment_1_times),
        (
            segment_2_points,
            segment_2_elevations,
            segment_2_times,
        ),
    ) = two_segment_py_data

    track = PyTrack(segment_1_points, segment_1_elevations, segment_1_times)

    track_overview_pre_add = track.get_track_overview()
    assert track.get_segment_overview(0) == track_overview_pre_add

    track.add_segmeent(segment_2_points, segment_2_elevations, segment_2_times)

    track_overview_post_add = track.get_track_overview()
    assert track_overview_pre_add != track_overview_post_add


@pytest.mark.parametrize("conn_segments", ["forward", "full"])
def test_track_data(
    mocker: MockerFixture,
    two_segment_py_data: tuple[tuple[list, list, list], tuple[list, list, list]],
    conn_segments: str,
) -> None:
    (
        (segment_1_points, segment_1_elevations, segment_1_times),
        (
            segment_2_points,
            segment_2_elevations,
            segment_2_times,
        ),
    ) = two_segment_py_data

    track = PyTrack(segment_1_points, segment_1_elevations, segment_1_times)

    spy_get = mocker.spy(track, "_get_processed_track_data")
    spy_set = mocker.spy(track, "_set_processed_track_data")

    assert track._processed_track_data == {}

    data_track = track.get_track_data(connect_segments=conn_segments)
    pt_segs, (_, _, _, _, pt_df) = track._processed_track_data[conn_segments]  # type: ignore
    assert pt_segs == 1
    assert isinstance(pt_df, pd.DataFrame)

    assert spy_get.call_count == 1
    assert spy_set.call_count == 1

    track.get_track_data(connect_segments=conn_segments)

    assert spy_get.call_count == 2
    assert spy_set.call_count == 1

    data_segment = track.get_segment_data(0)
    assert isinstance(data_track, pd.DataFrame)
    assert set(data_track.segment.unique()) == {0}
    assert data_segment.compare(data_track.drop(columns=["segment"])).empty

    track.add_segmeent(segment_2_points, segment_2_elevations, segment_2_times)
    data_track_post_add_seg = track.get_track_data(connect_segments=conn_segments)

    pt_segs, (_, _, _, _, pt_df) = track._processed_track_data[conn_segments]  # type: ignore
    assert pt_segs == 2
    assert isinstance(pt_df, pd.DataFrame)

    assert spy_set.call_count == 2
    assert spy_get.call_count == 3
    assert spy_get.call_count == 3

    assert isinstance(data_track_post_add_seg, pd.DataFrame)

    assert set(data_track_post_add_seg.segment.unique()) == {0, 1}


def test_split_track() -> None:
    track = PyTrack(
        [
            (1.0001, 1.0001),
            (1.00012, 1.00012),
            (1.00014, 1.00014),
            (1.00016, 1.00016),
            (1.00018, 1.00018),
            (1.0002, 1.0002),
        ],
        [100, 100, 100, 100, 100, 100],
        [
            datetime(2023, 1, 1, 10),
            datetime(2023, 1, 1, 10, 0, 10),
            datetime(2023, 1, 1, 10, 0, 20),
            datetime(2023, 1, 1, 10, 0, 30),
            datetime(2023, 1, 1, 10, 0, 40),
            datetime(2023, 1, 1, 10, 0, 50),
        ],
    )

    assert track.n_segments == 1
    pre_split_track_data = track.get_track_data()
    pre_split_segment_data = track.get_segment_data(0)

    track.split(coords=(1.000139, 1.000139))

    assert track.n_segments == 2
    assert track.track.segments[1].points[0].latitude == 1.00014
    assert track.track.segments[1].points[0].longitude == 1.00014

    post_split_track_data = track.get_track_data()
    post_split_segment_0_data = track.get_segment_data(0)
    post_split_segment_1_data = track.get_segment_data(1)

    assert not pre_split_track_data.compare(post_split_track_data).empty
    assert (
        pre_split_track_data.drop("segment", axis=1)
        .compare(post_split_track_data.drop("segment", axis=1))
        .empty
    )

    assert (
        len(pre_split_segment_data)
        == len(post_split_segment_0_data) + len(post_split_segment_1_data) + 1
    )


def test_split_exceed_threshold(track_for_test: Track) -> None:
    with pytest.raises(TrackTransformationError):
        track_for_test.split((1, 1))


@pytest.mark.parametrize("intervals", [None, 1, 200])
@pytest.mark.parametrize("segment", [None, 0])
@pytest.mark.parametrize(
    "kind",
    [
        "profile",
        "profile-slope",
        "map-line",
        "map-line-enhanced",
    ],
)
def test_plot_segment_indepenent(
    intervals: int | None, segment: int | None, kind: str
) -> None:
    resource_files = importlib.resources.files(resources)

    track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes()
    )
    fig = track.plot(kind, segment=segment, reduce_pp_intervals=intervals)

    assert isinstance(fig, Figure)


@pytest.mark.parametrize(
    "kind",
    ["map-segments"],
)
def test_plot_segment_plot(kind: str) -> None:
    resource_files = importlib.resources.files(resources)

    track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes()
    )

    track.split((47.9805, 7.84799))

    fig = track.plot(kind)  # type: ignore

    assert isinstance(fig, Figure)


@pytest.mark.parametrize(
    "kind",
    ["map-segments"],
)
def test_plot_multi_segment_plot(kind: str) -> None:
    resource_files = importlib.resources.files(resources)

    track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes()
    )

    track.split((47.9805, 7.84799))
    track.split((47.95591, 7.86402))
    track.split((47.940, 7.8682))

    fig = track.plot(kind, segment=[1, 2])  # type: ignore

    assert isinstance(fig, Figure)


@pytest.mark.parametrize(
    ("kind", "kwargs"),
    [
        ("segment_summary", {"aggregate": "total_distance"}),
        ("segment_box", {"metric": "elevation"}),
        ("zone_summary", {"metric": "heartrate", "aggregate": "distance"}),
        ("segment_zone_summary", {"metric": "heartrate", "aggregate": "distance"}),
    ],
)
def test_plot_segment_summaries(kind: str, kwargs: dict) -> None:
    resource_files = importlib.resources.files(resources)

    hr_zones = Zones(
        intervals=[
            ZoneInterval(start=None, end=130),
            ZoneInterval(start=130, end=160),
            ZoneInterval(start=160, end=None),
        ]
    )

    track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes(),
        heartrate_zones=hr_zones,
    )
    track.split((47.9805, 7.84799))
    fig = track.plot(kind, **kwargs)  # type: ignore
    assert isinstance(fig, Figure)


@pytest.mark.parametrize(
    ("kind", "kwargs"),
    [
        ("segment_summary", {}),
        ("segment_box", {}),
        ("zone_summary", {"aggregate": "distance"}),
        ("zone_summary", {"metric": "heartrate"}),
        ("segment_zone_summary", {"aggregate": "distance"}),
        ("segment_zone_summary", {"metric": "heartrate"}),
    ],
)
def test_plot_segment_summaries_kwarg_errors(kind: str, kwargs: dict) -> None:
    resource_files = importlib.resources.files(resources)

    hr_zones = Zones(
        intervals=[
            ZoneInterval(start=None, end=130),
            ZoneInterval(start=130, end=160),
            ZoneInterval(start=160, end=None),
        ]
    )

    track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes(),
        heartrate_zones=hr_zones,
    )
    track.split((47.9805, 7.84799))
    with pytest.raises(VisualizationSetupError):
        track.plot(kind, **kwargs)  # type: ignore


def test_plot_use_distance_segments(
    mocker: MockerFixture,
) -> None:
    import geo_track_analyzer.utils.track as track_utils_mod

    resource_files = importlib.resources.files(resources)

    spy_generate = mocker.spy(track_utils_mod, "generate_distance_segments")

    track = ByteTrack(
        (resource_files / "Freiburger_Münster_nach_Schau_Ins_Land.gpx").read_bytes(),
    )

    fig = track.plot("map-segments", use_distance_segments=1000)
    assert spy_generate.call_count == 1
    assert isinstance(fig, Figure)

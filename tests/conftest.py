from datetime import datetime

import pytest

from track_analyzer.track import PyTrack, Track


@pytest.fixture()
def track_for_test() -> Track:
    track = PyTrack(
        points=[
            (46.74025, 11.95624),
            (46.74027, 11.95587),
            (46.74013, 11.95575),
            (46.73946, 11.95588),
            (46.73904, 11.95627),
            (46.73852, 11.95609),
        ],
        elevations=[2248, 2247, 2244, 2245, 2252, 2256],
        times=[
            datetime(2023, 8, 1, 10),
            datetime(2023, 8, 1, 10, 1),
            datetime(2023, 8, 1, 10, 2),
            datetime(2023, 8, 1, 10, 3),
            datetime(2023, 8, 1, 10, 4),
            datetime(2023, 8, 1, 10, 5),
        ],
        heartrate=[100, 120, 125, 121, 125, 130],
        cadence=[80, 81, 79, 70, 60, 65],
        power=[150, 200, 200, 210, 240, 250],
    )

    track.add_segmeent(
        points=[
            (46.73861, 11.95697),
            (46.73862, 11.95755),
            (46.73878, 11.95778),
            (46.73910, 11.95763),
            (46.73930, 11.95715),
            (46.74021, 11.95627),
        ],
        elevations=[2263, 2268, 2270, 2269, 2266, 2248],
        times=[
            datetime(2023, 8, 1, 10, 6),
            datetime(2023, 8, 1, 10, 7),
            datetime(2023, 8, 1, 10, 8),
            datetime(2023, 8, 1, 10, 9),
            datetime(2023, 8, 1, 10, 9),
            datetime(2023, 8, 1, 10, 10),
        ],
        heartrate=[155, 160, 161, 150, 140, 143],
        cadence=[82, 83, 78, 71, 66, 69],
        power=[240, 230, 234, 220, 210, 200],
    )

    return track

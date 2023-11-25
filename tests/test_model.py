from geo_track_analyzer.model import SegmentOverview


def test_segment_overview_post_init_calcs():
    moving_distance = 1000
    total_distance = 12002
    max_speed = 8.333  # 30 km/h
    avg_speed = 5.556  # 20 km/h
    so = SegmentOverview(
        1000,
        1000,
        moving_distance,
        total_distance,
        max_speed,
        avg_speed,
        300,
        100,
        100,
        -200,
    )
    assert so.max_velocity_kmh == max_speed * 3.6
    assert so.avg_velocity_kmh == avg_speed * 3.6
    assert so.moving_distance_km == moving_distance / 1000
    assert so.total_distance_km == total_distance / 1000

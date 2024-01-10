from geo_track_analyzer.model import SegmentOverview


def test_segment_overview_post_init_calcs() -> None:
    moving_distance = 1000
    total_distance = 12002
    max_speed = 8.333  # 30 km/h
    avg_speed = 5.556  # 20 km/h
    so = SegmentOverview(
        moving_time_seconds=1000,
        total_time_seconds=1000,
        moving_distance=moving_distance,
        total_distance=total_distance,
        max_velocity=max_speed,
        avg_velocity=avg_speed,
        max_elevation=300,
        min_elevation=100,
        uphill_elevation=100,
        downhill_elevation=-200,
    )
    assert so.max_velocity_kmh == max_speed * 3.6
    assert so.avg_velocity_kmh == avg_speed * 3.6
    assert so.moving_distance_km == moving_distance / 1000
    assert so.total_distance_km == total_distance / 1000

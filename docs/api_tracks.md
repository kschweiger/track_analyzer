# Track Reference

Every track dataframe uses `speed_ms` (m/s), `distance_m` (m), `cum_distance_m`,
`cum_distance_moving_m`, and `cum_distance_stopped_m`. `FITTrack.get_track_data()`
also includes the FIT record extensions `enhanced_speed_ms` (m/s) and
`raw_distance_m` (m). Its `session_data` dictionary uses `avg_velocity_ms`,
`max_velocity_ms`, and `distance_m` for the corresponding session values.

::: geo_track_analyzer.track.GPXFileTrack
::: geo_track_analyzer.track.FITTrack
::: geo_track_analyzer.track.ByteTrack
::: geo_track_analyzer.track.PyTrack
::: geo_track_analyzer.track.SegmentTrack
::: geo_track_analyzer.track.GeoJsonTrack

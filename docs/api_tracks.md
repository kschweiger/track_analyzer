# Track Reference

`FITTrack.get_track_data()` includes the FIT record extensions `enhanced_speed_ms`
(meters per second) and `raw_distance_m` (meters). Its `session_data` dictionary
uses `avg_velocity_ms`, `max_velocity_ms`, and `distance_m` for those session
values. The shared calculated dataframe columns remain `speed` (m/s) and
`distance` (m).

::: geo_track_analyzer.track.GPXFileTrack
::: geo_track_analyzer.track.FITTrack
::: geo_track_analyzer.track.ByteTrack
::: geo_track_analyzer.track.PyTrack
::: geo_track_analyzer.track.SegmentTrack
::: geo_track_analyzer.track.GeoJsonTrack

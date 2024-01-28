from geo_track_analyzer.track import GPXFileTrack
from geo_track_analyzer.utils.base import init_logging

if __name__ == "__main__":
    init_logging(10)

    track = GPXFileTrack("tests/resources/Teilstueck_Schau_ins_land.gpx")

    track_w_segments = GPXFileTrack("tests/resources/Teilstueck_Schau_ins_land.gpx")
    track_w_segments.split((47.930904, 7.882410))

    track.plot(kind="profile", width=None, height=None).write_html(
        "docs/snippets/examples/visualization/profile_simple.html",
        full_html=False,
    )

    track.plot(
        kind="profile", include_heartrate=True, width=None, height=None
    ).write_html(
        "docs/snippets/examples/visualization/profile.html",
        full_html=False,
    )

    track.plot(kind="profile-slope", width=None, height=None).write_html(
        "docs/snippets/examples/visualization/profile_slope.html",
        full_html=False,
    )

    track.plot(kind="map-line", line_width=4, width=None, height=None).write_html(
        "docs/snippets/examples/visualization/map_line.html",
        full_html=False,
    )

    track_w_segments.plot(
        kind="map-segments", line_width=4, width=None, height=None
    ).write_html(
        "docs/snippets/examples/visualization/map_segments.html",
        full_html=False,
    )

    track.plot(kind="map-line-enhanced", width=None, height=None).write_html(
        "docs/snippets/examples/visualization/map_line_enhanced.html",
        full_html=False,
    )

    track.interpolate_points_in_segment(10, 0)

    track.plot(kind="map-line-enhanced", width=None, height=None).write_html(
        "docs/snippets/examples/visualization/map_line_enhanced_interpolated.html",
        full_html=False,
    )

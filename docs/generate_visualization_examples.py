import pandas as pd

from geo_track_analyzer.track import GPXFileTrack
from geo_track_analyzer.utils.base import init_logging
from geo_track_analyzer.visualize.summary import (
    plot_segment_box_summary,
    plot_segment_summary,
    plot_segment_zones,
    plot_track_zones,
)

if __name__ == "__main__":
    init_logging(10)

    import plotly.io as pio

    pio.templates.default = "plotly_dark"

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

    track_w_segments.plot(
        kind="profile", show_segment_borders=True, width=None, height=None
    ).write_html(
        "docs/snippets/examples/visualization/profile_w_segment_borders.html",
        full_html=False,
    )

    data = pd.read_csv("tests/resources/summary_test_data.csv", sep=";")

    for agg in ["time", "distance", "speed"]:
        plot_track_zones(data, "heartrate", agg, width=None, height=None).write_html(
            f"docs/snippets/examples/visualization/zone_summary_hr_{agg}.html",
            full_html=False,
        )

    plot_segment_zones(data, "heartrate", "time", width=None, height=None).write_html(
        "docs/snippets/examples/visualization/zone_segment_summary_hr_time.html",
        full_html=False,
    )

    for agg in ["total_time", "total_distance", "avg_speed", "max_speed"]:
        plot_segment_summary(data, agg, width=None, height=None).write_html(
            f"docs/snippets/examples/visualization/segment_summary_{agg}.html",
            full_html=False,
        )

    for metric in ["heartrate", "speed", "elevation"]:
        plot_segment_box_summary(data, metric, width=None, height=None).write_html(
            f"docs/snippets/examples/visualization/segment_box_{metric}.html",
            full_html=False,
        )

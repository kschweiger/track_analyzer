# Track visualization - Profiles and Maps

All visualizations are implemented using the [Plotly Graphing Library](https://plotly.com/python/). All methods and functions return a [Figure](https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html#id0>) objects to enable additonal customization of the plot outside of the package e.g. using the `update_layout` method.

## Elevations profiles

Multiple visualizations of the elevation profile of you tracks can be generated using the [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] method.

### Profile with and without additional data

Using `kind="profile"` in [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] will generate a figure with the distance on the x-axis and the elevation on the y-axis.
Internally this will call the [`plot_track_2d`][geo_track_analyzer.visualize.plot_track_2d] function. See the api documentation for all options that can be passed.

--8<-- "docs/snippets//examples/visualization/profile_simple.html"

Passing one of the boolean flags `include_velocity`, `include_heartrate`, `include_cadence`, or `include_power` will additonally plot the velocity, heartrate, cadence, or power on a secondary y-axis, respectively if available.
Heart Rate and Power are visualized as line plot

--8<-- "docs/snippets//examples/visualization/profile.html"

while the cadence is visualized with markers

--8<-- "docs/snippets//examples/visualization/profile_w_cadence_no_zones.html"

If [`Zones`][geo_track_analyzer.model.Zones] are set for Heart Rate, Cadence, or Power, these zones can be visualized in the profile plot by passing `split_by_zone` to the in [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] method or [`plot_track_2d`][geo_track_analyzer.visualize.plot_track_2d] function.

--8<-- "docs/snippets//examples/visualization/profile_w_cadence_zones.html"

### Profile with slopes

Using `kind="profile-slope"` in [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] will also generate a profile like before but additonally the slope between each point will be calcuated and viszalized in the plot by coloring the line and filling.
Depending on the density of the points by using the `reduce_pp_intervals` argument.
Internally this will call the [`plot_track_with_slope`][geo_track_analyzer.visualize.plot_track_with_slope] function. See the api documentation for all options that can be passed.

--8<-- "docs/snippets//examples/visualization/profile_slope.html"

Color scale and min/max slope can be configured using the `slope_gradient_color`, `min_slope`, and `max_slope` arguments as documented in [`plot_track_with_slope`][geo_track_analyzer.visualize.plot_track_with_slope].

### Displaying segments/laps in profile plots

Plots of kinds `profile-slope` and `profile` can show the segments (or laps) in a track by passing the `show_segment_borders` argument.
This add a vertical line at the distance corresponding to the first point in the segment. The color of the lien can be modified with by
passing `color_segment_border` with a valid color string for plotly.

--8<-- "docs/snippets//examples/visualization/profile_w_segment_borders.html"

## Map Visualizations

Multiple visualizations of the path of the track on a map can be generated using the [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] method. As default to
Open Streetmap style is used for map. By passing `map_style` with a valid Plotly Mapboxstyle value this can be changed.

### Line on map

Using `kind="map-line"` in [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] will generate a figure with the track path on a map.
Internally this will call the [`plot_track_line_on_map`][geo_track_analyzer.visualize.plot_track_line_on_map] function. See the api documentation for all options that can be passed.

--8<-- "docs/snippets//examples/visualization/map_line.html"

### Individual segments lines with summary data on map

Using `kind="map-segments"` in [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] will generate a figure with the track path on a map. This plot can only be generated if the Track contains
multiple segments. Otherwise an `VisualizationSetupError` will be raised. If two or more segments are present, the path will be split and colored into different segments and min/max/average of
elevation, speed, heartrate, cadence, and power will be shown when hovering over the segment.
Internally this will call the [`plot_segments_on_map`][geo_track_analyzer.visualize.plot_segments_on_map] function. See the api documentation for all options that can be passed.

--8<-- "docs/snippets//examples/visualization/map_segments.html"

### Line on map with additonal data

Using `kind="map-line-enhanced"` in [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] will generate a figure with the track path on a map.
Additionally elevation, speed, heartrate, cadence, or power will be added via the color of the path. Set by passing the `enrich_with_column` argument.
Internally this will call the [`plot_track_enriched_on_map`][geo_track_analyzer.visualize.plot_track_enriched_on_map] function. See the api documentation for all options that can be passed.

Unlike with the previous line plots, the individual track points are shown on the map and not the line connection consecutive points. For dense tracks this is no problem on normal zoom levels showing the whole track.
But gaps may appear for sparse tracks as show below.

--8<-- "docs/snippets//examples/visualization/map_line_enhanced.html"

Use the inerpolate feature [`Track.interpolate_points_in_segment`][geo_track_analyzer.GPXFileTrack.interpolate_points_in_segment] to increase the density with a following result:

--8<-- "docs/snippets//examples/visualization/map_line_enhanced_interpolated.html"

The line can also be colored based on the [`Zones`][geo_track_analyzer.model.Zones] set in the track for Heart Rate, Cadence, and Power by passing `color_by_zone=True` in the argument of [`Track.plot`][geo_track_analyzer.track.GPXFileTrack.plot] or [`plot_track_enriched_on_map`][geo_track_analyzer.visualize.plot_track_enriched_on_map].

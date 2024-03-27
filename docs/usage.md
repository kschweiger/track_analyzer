# Usage

## Installation

To use Geo-Track-Analyzer, first install it using pip:

```shell
pip install geo-track-analyzer
```

Installing the package with **cli** extra, I.e. using `pip install geo-track-analyzer[cli]`, add utility tools. See the [Command line interfaces](cli.md) page for details.


## Analyze geospacial tracks

The focus of this package lies on analyzing and visualizing tracks of cycling or similar activities. Depending on the usecase settings like `stopped_speed_threshold` or `max_speed_percentile` may not be appropriate.

### Initialize a track

Tracks my be initialized from `.gpx` and `.fit` files using the [`GPXFileTrack`][geo_track_analyzer.track.GPXFileTrack] and [`FITTrack`][geo_track_analyzer.track.FITTrack] object, respectively.

Furhtermore the Track can be initialized programmatically from python objects inside your code using

```python
    PyTrack(
        points: list[tuple[float, float]] = ...,
        elevations: None | list[float] = ...,
        times: None | list[datetime] = ...,
        heartrate: None | list[int] = None,
        cadence: None | list[int] = None,
        power: None | list[int] = None,
    )
```

#### Zones

When intiliazing a track, zones for `heartrate`, `power`, and `cadence` can be set and are used for further analysis of a track. For this defined the zones via the [`Zones`][geo_track_analyzer.model.Zones] object:

```python
Zones(
    intervals=[
        ZoneInterval(start=None, end=135),
        ZoneInterval(start=135, end=146),
        ZoneIntervayl(start=146, end=155),
        ZoneInterval(start=155, end=165),
        ZoneInterval(start=165, end=169),
        ZoneInterval(start=169, end=174),
        ZoneInterval(start=174, end=None),
    ]
)
```

Each [`ZoneInterval`][geo_track_analyzer.model.ZoneInterval] can also be defined with a `name` and a `color` attribute for further customization. For the interval definition, it is enforced

- that the first (last) interval starts (ends) with a `None` value and
- that consecutive intervals end/start with the same value.


### Extracting track data

The data of the track can be extracted into a pandas DataFrame object with the columns:

* *latitude*: Track point latitude value
* *longitude*: Track point longitude value
* *elevation*: Track point elevation value
* *speed*: Speed in m/s calculated relative to previous point. Requires time to be present in track.
* *distance*: Distance in m relative to previous point
* *heartrate*: Heartrate in bpm (if present in input)
* *cadence*: Cadence in rmp(if present in input)
* *power*: Power in W (if present in input)
* *time*: Time in seconds relative to previous point. Time must be present in track.
* *cum_time*: Cummulated time of the track/segment in seconds.  Requires time to be present in track.
* *cum_time_moving*: Cummulated moving time of the track/segment in seconds.  Requires time to be present in track.
* *cum_distance*: Cummulated distance in track/segement in meters.
* *cum_distance_moving*:  Cummulated moving distance in track/segement in meters.
* *cum_distance_stopped*:  Cummulated stopped distance in track/segement in meters.
* *moving*: Bool flag specifing if the `stopped_speed_threshold` was exceeded for the point.

Because some values are relative to previous points, the first point in the segment is not represented in this dataframe.

----------------

Furthermore an summary of the segments and tracks can be generated in the form of a [`SegmentOverview`][geo_track_analyzer.model.SegmentOverview] containing:

* Time in seconds (moving and totoal)
* Distance in meters and km (moving and totoal)
* Maximum and average velocity in m/s and km/h
* Maximum and minimum elevation in meters
* Uphill and downhill elevation in meters

### Visualizing the track


Visualizations of a track can be generated via the [`Track.plot`][geo_track_analyzer.GPXFileTrack.plot] method via the `kind` parameter. Additionally the
track data can be extracted with the [`Track.get_track_data`][geo_track_analyzer.GPXFileTrack.get_track_data] or [`Track.get_segment_data`][geo_track_analyzer.GPXFileTrack.get_segment_data]
methods and using the functions described in the [Profiles and Maps](vis_profiles_and_maps.md) and [Summaries](vis_summaries.md).
[![Testing](https://github.com/kschweiger/track_analyzer/actions/workflows/test.yml/badge.svg)](https://github.com/kschweiger/track_analyzer/actions/workflows/test.yml)
[![Build Documentation](https://github.com/kschweiger/track_analyzer/actions/workflows/doc.yml/badge.svg)](https://github.com/kschweiger/track_analyzer/actions/workflows/doc.yml)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/geo-track-analyzer)
![PyPI - License](https://img.shields.io/pypi/l/geo-track-analyzer)
![PyPI - Version](https://img.shields.io/pypi/v/geo-track-analyzer)


# Track analyzer

The focus of this package lies on analyzing and visualizing tracks of cycling or similar activities. Depending on the usecase settings like `stopped_speed_threshold` or `max_speed_percentile` may not be appropriate.

Installing the package with **cli** extra, I.e. using `pip install geo-track-analyzer[cli]`, add utility tools. See the [documentation](https://kschweiger.github.io/track_analyzer/cli/) for details.

## From files

Tracks my be initialized from ``.gpx`` and ``.fit`` files using the ``GPXFileTrack`` and ``FITTrack`` object, respectively.


## Programmatically

You can instanciate tracks programmatically inside your code using the `PyTrack` class.

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
## Extracting track data

The data of the track can be extracted into a pandas DataFrame object with the columns:

* **latitude**: Track point latitude value
* **longitude**: Track point longitude value
* **elevation**: Track point elevation value
* **speed**: Speed in m/s calculated relative to previous point. Requires time to be present in track.
* **distance**: Distance in m relative to previous point
* **heartrate**: Heartrate in bpm (if present in input)
* **cadence**: Cadence in rmp(if present in input)
* **power**: Power in W (if present in input)
* **time**: Time in seconds relative to previous point. Time must be present in track.
* **cum_time**: Cummulated time of the track/segment in seconds.  Requires time to be present in track.
* **cum_time_moving**: Cummulated moving time of the track/segment in seconds.  Requires time to be present in track.
* **cum_distance**: Cummulated distance in track/segement in meters.
* **cum_distance_moving**:  Cummulated moving distance in track/segement in meters.
* **cum_distance_stopped**:  Cummulated stopped distance in track/segement in meters.
* **moving**: Bool flag specifing if the `stopped_speed_threshold` was exceeded for the point.

Because some values are relative to previous points, the first point in the segment is not represented in this dataframe.

----------------

Furthermore an summary of the segments and tracks can be generated in the form of a `SegmentOverview` containing:

* Time in seconds (moving and totoal)
* Distance in meters and km (moving and totoal)
* Maximum and average velocity in m/s and km/h
* Maximum and minimum elevation in meters
* Uphill and downhill elevation in meters

## Visualizing the track

Visualizations of a track can be generated via the `plot` method and the ``kind`` parameter. See [documentation](https://kschweiger.github.io/track_analyzer/visualizations/) for further details and examples how to use the visualizations.
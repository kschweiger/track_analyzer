# Track analyzer

Package aims to define a common interface for analyzing and visualizing geospacial data tracks from various sources.

## From files

Currently `.gpx` and `.fit` files are supported. Use the `GPXFileTrack("path/to/file.gpx")` and `FITFileTrack("path/to/file.fit")` in order to load the data into the interface.

## Programmatically

You can instanciate tracks programmatically inside your code using the `PyTrack` class.

```python
class PyTrack(Track):
    def __init__(
        self,
        points: list[tuple[float, float]],
        elevations: None | list[float],
        times: None | list[datetime],
        heartrate: None | list[int] = None,
        cadence: None | list[int] = None,
        power: None | list[int] = None,
        **kwargs,
    )
```

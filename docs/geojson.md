# GeoJSON support

The track enhancer support loading specific configurations of valid GeoJSON file via the [`GeoJsonTrack`][geo_track_analyzer.track.GeoJsonTrack].

???+ warning "Warning"

    The order in the cooordinates array must be [longitude, latitude, elevation] and not [latitude, longitude, elevation]. This is a common mistake when working with GeoJSON data and can lead to incorrect results if not handled properly.

The following example for all three configurations that are supported.

The use does not need to specify in advance which configuration is used. On initialization, it is automatically determined based on the input structure. If no valid configuration is found, a `UnsupportedGeoJsonTypeError` is raised.

Additionally, it is possible to load GeoJSON files that do not contain any geometry. While this seems like a silly feature in a "track analyzer", it provides the option to visualize files that contain for example heart rate as a function of time. By default, a `GeoJsonWithoutGeometryError` is raised. But the `allow_empty_spatial` flag can be passed to enable this feature. In this case the internal gpx track (or the one you would get by exporting the [`GeoJsonTrack`][geo_track_analyzer.track.GeoJsonTrack] to xml) with the coordinates set with `fallback_coordinates` defaulting to (0,0). Also, this disables the moving/stopped logic in the segment data (every point is considered moving in that case).

## LineString + Arrays

Here the coordinates are stored as a LineString geometry and the time, heart rate, cadence and power values are stored as arrays in the properties. The arrays must be of the same length as the number of coordinates in the LineString.

```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [13.404954, 52.520008, 30.5],
      [13.405000, 52.520100, 31.0],
      [13.405100, 52.520200, 31.2]
    ]
  },
  "properties": {
    "name": "Morning Ride",
    "coordTimes": [
      "2023-10-01T08:00:00Z",
      "2023-10-01T08:00:05Z",
      "2023-10-01T08:00:10Z"
    ],
    "heartRates": [140, 142, 145]
    "cadences": [85, 87, 88],
    "powers": [200.5, 205.3, 210.0],
  }
}
```

### With multiple segments

Multiple segments can be represented as multiple features in a FeatureCollection and is *only* available in the __LineString + Arrays__ configuration. Each feature must have a `segment_index` property that indicates the index of the segment in the track. The `coordTimes`, `heartRates`, `cadences`, and `powers` properties must be arrays of the same length as the number of coordinates in the LineString geometry of the feature.

```json
{
  "type": "FeatureCollection",
  "properties": {
    "name": "Morning Ride with Pause"
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "segment_index": 0,
        "coordTimes": [
          "2023-10-01T08:00:00Z",
          "2023-10-01T08:00:05Z"
        ],
        "heartRates": [140, 142]
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [13.404954, 52.520008, 30.5],
          [13.405000, 52.520100, 31.0]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "segment_index": 1,
        "coordTimes": [
          "2023-10-01T08:15:00Z",
          "2023-10-01T08:15:05Z"
        ],
        "heartRates": [135,138]
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [13.405100,52.520200, 31.2],
          [13.405200, 52.520300, 31.5]
        ]
      }
    }
  ]
}
```





## Collection of Points

In this case the data is fully represented by a FeatureCollection and each feature represents a single point in the track. The time, heart rate, cadence and power values are stored as properties of each feature. The geometry of each feature must be a Point geometry with the coordinates representing the latitude, longitude and elevation of the point.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [13.404954, 52.520008, 30.5]
      },
      "properties": {
        "time": "2023-10-01T08:00:00Z",
        "heartRate": 140,
        "cadence": 85
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [13.405000, 52.520100, 31.0]
      },
      "properties": {
        "time": "2023-10-01T08:00:05Z",
        "heartRate": 142,
        "cadence": 87
      }
    }
  ]
}
```



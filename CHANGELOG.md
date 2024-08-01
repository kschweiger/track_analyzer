<!-- insertion marker -->
<a name="1.4.3"></a>

## [1.4.3](https://github.com/kschweiger/track_analyzer/compare/1.4.2...1.4.3) (2024-08-01)

<a name="1.4.2"></a>

## [1.4.2](https://github.com/kschweiger/track_analyzer/compare/1.4.1...1.4.2) (2024-08-01)

<a name="1.4.1"></a>

## [1.4.1](https://github.com/kschweiger/track_analyzer/compare/1.4.0...1.4.1) (2024-08-01)

### Bug Fixes

- **profiles:** Velocity could not be plotted as secondary due to column/name conflict ([41132db](https://github.com/kschweiger/track_analyzer/commit/41132db5a8358a7ed0a007eddb72463fc0ed7b32))

<a name="1.4.0"></a>

## [1.4.0](https://github.com/kschweiger/track_analyzer/compare/1.3.2...1.4.0) (2024-05-25)

### Features

- Zones and summary plots (#23) ([7be77d0](https://github.com/kschweiger/track_analyzer/commit/7be77d0181ba7027a0ba1dfd4b58d357637f52de))

<a name="1.3.2"></a>

## [1.3.2](https://github.com/kschweiger/track_analyzer/compare/1.3.1...1.3.2) (2024-04-09)

### Bug Fixes

- **profiles:** Segment border crashed with partial data (#24) ([5cf727f](https://github.com/kschweiger/track_analyzer/commit/5cf727f29968dc7b4ed65c5106d3259165e96ffd))

<a name="1.3.1"></a>

## [1.3.1](https://github.com/kschweiger/track_analyzer/compare/1.3.0...1.3.1) (2024-03-02)

### Bug Fixes

- **visualization:** Segment borders in profile plots are now drawn at the correct points ([f5b71b9](https://github.com/kschweiger/track_analyzer/commit/f5b71b92b4491c9205c11e2a1b4a06e2706b597b))

<a name="1.3.0"></a>

## [1.3.0](https://github.com/kschweiger/track_analyzer/compare/1.2.0...1.3.0) (2024-03-02)

### Features

- **visualization:** Profile plots can display borders between segments/laps in track ([2c18cd8](https://github.com/kschweiger/track_analyzer/commit/2c18cd84d2ad3880fde4d06fb0af48a8fc21bc4d))
- **Track:** plot method can be constrained to a subset of segments (#19) ([56adca4](https://github.com/kschweiger/track_analyzer/commit/56adca406731eb8b85d169c519228623711b88f0))
- **FITTrack:** Save laps as segments and deal with missing elevation data ([9beb65a](https://github.com/kschweiger/track_analyzer/commit/9beb65adbd461de82ef962cfc805940ebb66f93f))

<a name="1.2.0"></a>

## [1.2.0](https://github.com/kschweiger/track_analyzer/compare/1.1.2...1.2.0) (2024-01-28)

### Code Refactoring

- **get_closest_point:** n_segment type hint and docstring reflects that full track can be used ([453d0dd](https://github.com/kschweiger/track_analyzer/commit/453d0dd77ee386f36671265c98ea406db872b2e5))
- cli tools are available via extra cli (#17) ([712e59c](https://github.com/kschweiger/track_analyzer/commit/712e59c42ccc32027387a87a05268ec2b3a9200b))

<a name="1.1.2"></a>

## [1.1.2](https://github.com/kschweiger/track_analyzer/compare/1.1.1...1.1.2) (2024-01-14)

<a name="1.1.1"></a>

## [1.1.1](https://github.com/kschweiger/track_analyzer/compare/1.1.0...1.1.1) (2024-01-13)

<a name="1.1.0"></a>

## [1.1.0](https://github.com/kschweiger/track_analyzer/compare/1.0.0...1.1.0) (2024-01-13)

### Features

- Convert model dataclasses to pydantic models  (#16) ([488600b](https://github.com/kschweiger/track_analyzer/commit/488600b9e069a3a4234abb20d09469ea508629a9))
- enhance-elevation cli (#15) ([9318d93](https://github.com/kschweiger/track_analyzer/commit/9318d93612ad3aa01673c385a8d8cae36487d5d3))
- **visualize:** Adding function for plotting data of multiple tracks ([9b96054](https://github.com/kschweiger/track_analyzer/commit/9b96054e1fe5b75e682954e2db5de01ac1e6da06))

<a name="1.0.0"></a>

## [1.0.0](https://github.com/kschweiger/track_analyzer/compare/0.5.3...1.0.0) (2023-12-04)

<a name="0.5.3"></a>

## [0.5.3](https://github.com/kschweiger/track_analyzer/compare/0.5.2...0.5.3) (2023-12-04)

<a name="0.5.2"></a>

## [0.5.2](https://github.com/kschweiger/track_analyzer/compare/0.5.1...0.5.2) (2023-12-04)

<a name="0.5.1"></a>

## [0.5.1](https://github.com/kschweiger/track_analyzer/compare/0.5.0...0.5.1) (2023-12-03)

<a name="0.5.0"></a>

## [0.5.0](https://github.com/kschweiger/track_analyzer/compare/0.4.1...0.5.0) (2023-12-03)

### Features

- Interpolation includes extentions heartrate, cadence, power (#13) ([e777fa1](https://github.com/kschweiger/track_analyzer/commit/e777fa1505b28fc3e626ecb0fdcaba23ebaa0231))
- Merge pull request #12 from kschweiger/doc: ([74dc4a2](https://github.com/kschweiger/track_analyzer/commit/74dc4a29632e4b616c20a27553036cc468af6960))
- **visualize.map:** Adding map_style and line_width for map plot functions ([0beaec2](https://github.com/kschweiger/track_analyzer/commit/0beaec264093dd03c11e3e755a9b70d7aa6dbcb1))
- **Track:** Adding split method (#11) ([3ac4a42](https://github.com/kschweiger/track_analyzer/commit/3ac4a427f2a46300c6aba56f58b44a6a5e953e51))
- **Track:** Added plot method (#9) ([d71b888](https://github.com/kschweiger/track_analyzer/commit/d71b88821ae48b6b6bf2348ddad8793ad21a5f74))

### Bug Fixes

- **plot_segments_on_map:** Plot now works with tracks w/o time ([4789ddb](https://github.com/kschweiger/track_analyzer/commit/4789ddb300ceadd1907a9ab402a11a5068703581))
- Track DataFrame with multiple segments was missing datapoints ([975f1f9](https://github.com/kschweiger/track_analyzer/commit/975f1f9f5e695fe11cd1c38740692aa4282a62dd))

### Code Refactoring

- Renamed package to geo-track-analyzer ([13779ef](https://github.com/kschweiger/track_analyzer/commit/13779eff5622d3351cb0143419adf7bf0e902acf))

<a name="0.4.1"></a>

## [0.4.1](https://github.com/kschweiger/track_analyzer/compare/0.4.0...0.4.1) (2023-10-15)

### Code Refactoring

- **FITTrack:** Adapt FITTrack init to reflect that bytes can be passed directly ([7f368ae](https://github.com/kschweiger/track_analyzer/commit/7f368ae182251cd25069048bf176d94f11d4bf89))

<a name="0.4.0"></a>

## [0.4.0](https://github.com/kschweiger/track_analyzer/compare/0.3.2...0.4.0) (2023-10-10)

### Features

- Implemented splitting function ([429763d](https://github.com/kschweiger/track_analyzer/commit/429763dc1379bbc10405609a9ce3d445e6430153))
- Added plot method for shown different segments in track with segment metrics ([b88a9d2](https://github.com/kschweiger/track_analyzer/commit/b88a9d2160ba7b9100900cd861e7abe71fe64fec))
- **plot_track_enriched_on_map:** Deal with nan's in data used to enrich plot ([ba16c33](https://github.com/kschweiger/track_analyzer/commit/ba16c33cc7639b1fcd5611f9f04479bf219df008))
- Added plot that shows track on map and enriches the visualization with an additonal metric ([036cfe0](https://github.com/kschweiger/track_analyzer/commit/036cfe0d28d1e78781b3bcdeb6be4bb8d44831bb))
- **plot_track_with_slope:** Function can be run for segments of full tracks ([1a4cc29](https://github.com/kschweiger/track_analyzer/commit/1a4cc294ee803ab1e995b5127b79e912b860fee0))
- Added method to get overall track DataFrame ([5881dd1](https://github.com/kschweiger/track_analyzer/commit/5881dd1cfa8e0fbdcb217266b5344966647b8641))
- Added track overview ([731d1ab](https://github.com/kschweiger/track_analyzer/commit/731d1abb80f3e34ddf0a79c6ab9313b2b4cc07fa))
- **Track:** Added add_segment method ([8c30cb6](https://github.com/kschweiger/track_analyzer/commit/8c30cb6638f9471b1bf3b6e9a780fb39a85817cf))

### Bug Fixes

- **_recalc_cumulated_columns:** Method did not consider data w/o time entries ([eab717b](https://github.com/kschweiger/track_analyzer/commit/eab717b29eadce31251942076c24f5ffc590a868))
- Fixed issue with cumulative values in precessed track data with multiple segments ([8123a53](https://github.com/kschweiger/track_analyzer/commit/8123a5316c68987da5e6df398d9eb4a71ab5f964))

### Code Refactoring

- Moved PointDistance to model.py ([5590f5e](https://github.com/kschweiger/track_analyzer/commit/5590f5e71535ec3fe27d9885fe16acb87358ee7f))
- Moved plot method to sub-package ([7a5d6d1](https://github.com/kschweiger/track_analyzer/commit/7a5d6d12c864d31d0d27199cb5c034b06b5e8d38))
- Renamed plot_track_on_map to plot_track_line_on_map ([7997d37](https://github.com/kschweiger/track_analyzer/commit/7997d37e1c42c744fc55d1f50a296e148c13544f))
- **get_point_distance:** Generalized get_point_distance_in_segment for tracks and renamed method ([9dbc0b7](https://github.com/kschweiger/track_analyzer/commit/9dbc0b7b7606fc490da3de772a0e5da62c68b1fe))
- Moved logic for generating the processed track data to processing.py and adapted Track code accordingly ([0f042d0](https://github.com/kschweiger/track_analyzer/commit/0f042d036878447b42f020109c9513bbbae437da))
- processed data are private attributes ([40a353d](https://github.com/kschweiger/track_analyzer/commit/40a353d0c599acbb1e496ff2a5a3403344c9fcbf))

<a name="0.3.2"></a>

## [0.3.2](https://github.com/kschweiger/track_analyzer/compare/0.3.1...0.3.2) (2023-09-03)

<a name="0.3.1"></a>

## [0.3.1](https://github.com/kschweiger/track_analyzer/compare/0.3.0...0.3.1) (2023-09-03)

### Bug Fixes

- **plot_track_2d:** Deal with nan values in heartrate, cadence, and power ([8620ef7](https://github.com/kschweiger/track_analyzer/commit/8620ef724e89601a9c7b3871140d957100a0ca48))

<a name="0.3.0"></a>

## [0.3.0](https://github.com/kschweiger/track_analyzer/compare/0.2.0...0.3.0) (2023-09-03)

### Features

- Adding heartrate, cadence, and power to 2d plot ([b303fc3](https://github.com/kschweiger/track_analyzer/commit/b303fc387e537debe2a70fc2be86064800bf6429))

### Code Refactoring

- Renamed FileTrack too GPXFileTrack and FITTrack to FITFileTrack ([3738082](https://github.com/kschweiger/track_analyzer/commit/373808257c5cf31c930933cc44ce5e6c762b1946))

<a name="0.2.0"></a>

## [0.2.0](https://github.com/kschweiger/track_analyzer/compare/0.1.2...0.2.0) (2023-09-02)

### Features

- Adding heartrate, cadence, and power Track and segment data processing ([dbf02b9](https://github.com/kschweiger/track_analyzer/commit/dbf02b976a97bf3e7abf256c4ff5d257a93cbc7c))

### Code Refactoring

- Removed 3.9 support and moved to now typing style ([64dd42f](https://github.com/kschweiger/track_analyzer/commit/64dd42f412ccd99d8e4bd0f20872c74ab5c5760f))
- Renamed package to track_analyzer ([f6db3bc](https://github.com/kschweiger/track_analyzer/commit/f6db3bc16521163391fc8951973ffe4c7748ab23))

<a name="0.1.2"></a>

## [0.1.2](https://github.com/kschweiger/track_analyzer/compare/0.1.1...0.1.2) (2023-06-11)

### Features

- Added basic support for fit file ([2563996](https://github.com/kschweiger/track_analyzer/commit/2563996009f8aa22f730581b6d5e0b297a142911))

### Bug Fixes

- **calc_elevation_metrics:** Deal with ZeroDivisionError ([8f66763](https://github.com/kschweiger/track_analyzer/commit/8f66763755efe14ef3b71d60fe2466a41698901e))

<a name="0.1.1"></a>

## [0.1.1](https://github.com/kschweiger/track_analyzer/compare/0.1.0...0.1.1) (2023-04-22)

### Features

- **get_segment_overlap:** Subsegments are merged if spearated by few points ([a33a3bc](https://github.com/kschweiger/track_analyzer/commit/a33a3bc85ad14992394cd064b5b33b40ff27fe01))

<a name="0.1.0"></a>

## [0.1.0](https://github.com/kschweiger/track_analyzer/compare/0.0.8...0.1.0) (2023-04-18)

### Features

- Implement methods for finding overlapping subsegments in tracks (#2) ([237b481](https://github.com/kschweiger/track_analyzer/commit/237b4810def7660a2d7d6fe030cd0653e823a64b))

<a name="0.0.8"></a>

## [0.0.8](https://github.com/kschweiger/track_analyzer/compare/0.0.7...0.0.8) (2023-03-11)

### Features

- **visualize:** Added option to add a x-axis slider to the 2d plots ([34febac](https://github.com/kschweiger/track_analyzer/commit/34febac79f6cd32b8e0f45390f588aa526c09355))

<a name="0.0.7"></a>

## [0.0.7](https://github.com/kschweiger/track_analyzer/compare/0.0.6...0.0.7) (2023-03-07)

### Bug Fixes

- Fixed axis titles in elevation plot with slope ([b62547d](https://github.com/kschweiger/track_analyzer/commit/b62547d93087dd24bc00543ae54fb52b05603452))

<a name="0.0.6"></a>

## [0.0.6](https://github.com/kschweiger/track_analyzer/compare/0.0.5...0.0.6) (2023-03-07)

### Bug Fixes

- Added tag creation to release.zsh ([817d3a5](https://github.com/kschweiger/track_analyzer/commit/817d3a58cc9dcd8a71dd806e63a8d2fb45a13b18))

<a name="0.0.5"></a>

## [0.0.5](https://github.com/kschweiger/track_analyzer/compare/0.0.2...0.0.5) (2023-03-07)

### Features

- Adding function for plotting the elevation profile of a track with slopes (#1) ([e6b54ec](https://github.com/kschweiger/track_analyzer/commit/e6b54ecc919cb397e6e5bab82bdbe797732925ec))

### Bug Fixes

- **calc_elevation_metrics:** Fixed possibility for zero division error ([908446a](https://github.com/kschweiger/track_analyzer/commit/908446a5360b75b0ce28a83b3d4bcd10e7b2a63e))

<a name="0.0.2"></a>

## [0.0.2](https://github.com/kschweiger/track_analyzer/compare/0.0.1...0.0.2) (2023-01-30)

### Features

- **Track:** Added to_xml method ([10af4e9](https://github.com/kschweiger/track_analyzer/commit/10af4e9fedd230fb2a4103cc8102990ed88fa704))
- **Track:** Added method for retrieving coordinates, elevations and times of the points in a segment ([be38442](https://github.com/kschweiger/track_analyzer/commit/be38442285a1570a64cade29b06ae9c370605cf8))
- **Track:** Added linear interpolation method ([23f6d95](https://github.com/kschweiger/track_analyzer/commit/23f6d95c08b6f1dca7f80a9ea4a4fbced21440f2))
- **plot_track_2d:** Added optional POIs to the plot; Color can be passed as arguement; Updated requires upgrade of plotly to >= 5.11 ([3679319](https://github.com/kschweiger/track_analyzer/commit/3679319111400838d462c1ea16e81add36c59232))
- **enhancer:** Added enhancer factory; Renamed Exception; Added inplace option to enhance_track method ([47e6054](https://github.com/kschweiger/track_analyzer/commit/47e6054247cb980b6c59d9001cde13a7449b596e))
- **PyTrack:** Added a Track that is initialized with python objects for points, elevation and time ([2c27312](https://github.com/kschweiger/track_analyzer/commit/2c27312962d1274793bf9fa7be0bc565143f2e72))

### Code Refactoring

- **Track:** Setting cum_distance_moving equal to cum_distance as all points are considered moving in segment data w/o times ([fda1957](https://github.com/kschweiger/track_analyzer/commit/fda1957a2a1d23f88252c28f1e2154a72f6d687f))
- **OpenTopoElevationEnhancer:** Added skip_checks argument ([194f5cb](https://github.com/kschweiger/track_analyzer/commit/194f5cb6df1eb620d4e1a921c603cb7e68022613))
- **Track:** Changed default value of the moving in segment data w/o times ([9924113](https://github.com/kschweiger/track_analyzer/commit/99241131691a49221c2d717a8d9a15977be2dbc5))

<a name="0.0.1"></a>

## [0.0.1](https://github.com/kschweiger/track_analyzer/compare/68f9de7880d94e285d2227db5724599e8bf501cb...0.0.1) (2022-09-09)

### Features

- Added plotting track on open-street-map ([81c4ed2](https://github.com/kschweiger/track_analyzer/commit/81c4ed2846dc6de2806eeff42b2eb79287781ab9))
- Added script for approximate the center of a list of latitude, longitude pairs ([58fba8f](https://github.com/kschweiger/track_analyzer/commit/58fba8fea392cd09ca46290ed3f285bd636e31ba))
- Added plotting functions ([486e4bd](https://github.com/kschweiger/track_analyzer/commit/486e4bd2775d4e0b9cf6e25ae2e2f6e65474164c))
- **ByteTrack:** Added Track that loads from a byte object ([ff18914](https://github.com/kschweiger/track_analyzer/commit/ff189149191901e85fbc1cde5b9280bbcd2e18ee))
- Added Elevation enhancer using OpenTopo api ([01d6139](https://github.com/kschweiger/track_analyzer/commit/01d6139cfe0a8af88f5a3ff8a1848adab714bb1e))
- Added main track analysis class ([a467e43](https://github.com/kschweiger/track_analyzer/commit/a467e430f8af2b550508eda4ad31766e21ec6092))
- Added classes used to enhance tracks. This commit adds OpenElevationEnhancer that used an open-elevation api the enhance the elevation in a track ([5b5a740](https://github.com/kschweiger/track_analyzer/commit/5b5a7407ea2c3916c82e236b18a524509e107375))
- Added datacalsses and some basic utility functions ([7d4313e](https://github.com/kschweiger/track_analyzer/commit/7d4313ef975ad78135aa93f1e1c5e298322b90e5))

### Bug Fixes

- Addressed a Value error in the asin calculation ([2f49d19](https://github.com/kschweiger/track_analyzer/commit/2f49d19fda3357f1e7de7da47ae4c1b7eda57bea))

### Code Refactoring

- **visualize:** Minor changes to plot2d ([a5d15ab](https://github.com/kschweiger/track_analyzer/commit/a5d15ab725622a726b462ae72f2fc7476083325b))
- Moved tests ([14b447a](https://github.com/kschweiger/track_analyzer/commit/14b447aa98623962c3e8462004d3aa806002dfd9))
- Refactored _get_processed_data_for_segment to use a DataFrame ([9921d4a](https://github.com/kschweiger/track_analyzer/commit/9921d4aef714e4611be559e457ad1afe39819929))


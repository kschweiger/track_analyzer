For a more detailed changelog see [CHANGELOG](https://github.com/kschweiger/track_analyzer/blob/main/CHANGELOG.md) on GitHub
## [1.6.0](https://github.com/kschweiger/track_analyzer/releases/tag/1.6.0)
### [1.6.0](https://github.com/kschweiger/track_analyzer/compare/1.5.0...1.6.0) (2024-11-06)

#### Features

- **plot_track_zones:** Add option to visualize as Pie Chart ([5ad0669](https://github.com/kschweiger/track_analyzer/commit/5ad0669c3b5e36e5cd8666171b32871a47bf3fb7))

<a name="1.5.0"></a>

----------------------------

## [1.5.0](https://github.com/kschweiger/track_analyzer/releases/tag/1.5.0)
### [1.5.0](https://github.com/kschweiger/track_analyzer/compare/1.4.4...1.5.0) (2024-10-23)

#### Features

- **track:** Add method for stripping track of all but one segment and removing specific segments (#26) ([cbc1ec5](https://github.com/kschweiger/track_analyzer/commit/cbc1ec5d6c61b13175e885bacdec1f92ef71837c))

<a name="1.4.4"></a>

----------------------------

## [1.4.4](https://github.com/kschweiger/track_analyzer/releases/tag/1.4.4)
### [1.4.4](https://github.com/kschweiger/track_analyzer/compare/1.4.3...1.4.4) (2024-08-02)

<a name="1.4.3"></a>

----------------------------

## [1.4.3](https://github.com/kschweiger/track_analyzer/releases/tag/1.4.3)
### [1.4.3](https://github.com/kschweiger/track_analyzer/compare/1.4.2...1.4.3) (2024-08-01)

<a name="1.4.2"></a>

----------------------------

## [1.4.2](https://github.com/kschweiger/track_analyzer/releases/tag/1.4.2)
### [1.4.2](https://github.com/kschweiger/track_analyzer/compare/1.4.1...1.4.2) (2024-08-01)

<a name="1.4.1"></a>

----------------------------

## [1.4.1](https://github.com/kschweiger/track_analyzer/releases/tag/1.4.1)
### [1.4.1](https://github.com/kschweiger/track_analyzer/compare/1.4.0...1.4.1) (2024-08-01)

#### Bug Fixes

- **profiles:** Velocity could not be plotted as secondary due to column/name conflict ([41132db](https://github.com/kschweiger/track_analyzer/commit/41132db5a8358a7ed0a007eddb72463fc0ed7b32))

<a name="1.4.0"></a>

----------------------------

## [1.4.0](https://github.com/kschweiger/track_analyzer/releases/tag/1.4.0)
### [1.4.0](https://github.com/kschweiger/track_analyzer/compare/1.3.2...1.4.0) (2024-05-25)

#### Features

- Zones and summary plots (#23) ([7be77d0](https://github.com/kschweiger/track_analyzer/commit/7be77d0181ba7027a0ba1dfd4b58d357637f52de))

<a name="1.3.2"></a>

----------------------------

## [1.3.2](https://github.com/kschweiger/track_analyzer/releases/tag/1.3.2)
### [1.3.2](https://github.com/kschweiger/track_analyzer/compare/1.3.1...1.3.2) (2024-04-09)

#### Bug Fixes

- **profiles:** Segment border crashed with partial data (#24) ([5cf727f](https://github.com/kschweiger/track_analyzer/commit/5cf727f29968dc7b4ed65c5106d3259165e96ffd))

<a name="1.3.1"></a>

----------------------------

## [1.3.1](https://github.com/kschweiger/track_analyzer/releases/tag/1.3.1)
### [1.3.1](https://github.com/kschweiger/track_analyzer/compare/1.3.0...1.3.1) (2024-03-02)

#### Bug Fixes

- **visualization:** Segment borders in profile plots are now drawn at the correct points ([f5b71b9](https://github.com/kschweiger/track_analyzer/commit/f5b71b92b4491c9205c11e2a1b4a06e2706b597b))

<a name="1.3.0"></a>

----------------------------

## [1.3.0](https://github.com/kschweiger/track_analyzer/releases/tag/1.3.0)
### [1.3.0](https://github.com/kschweiger/track_analyzer/compare/1.2.0...1.3.0) (2024-03-02)

#### Features

- **visualization:** Profile plots can display borders between segments/laps in track ([2c18cd8](https://github.com/kschweiger/track_analyzer/commit/2c18cd84d2ad3880fde4d06fb0af48a8fc21bc4d))
- **Track:** plot method can be constrained to a subset of segments (#19) ([56adca4](https://github.com/kschweiger/track_analyzer/commit/56adca406731eb8b85d169c519228623711b88f0))
- **FITTrack:** Save laps as segments and deal with missing elevation data ([9beb65a](https://github.com/kschweiger/track_analyzer/commit/9beb65adbd461de82ef962cfc805940ebb66f93f))

<a name="1.2.0"></a>

----------------------------

## [1.2.0](https://github.com/kschweiger/track_analyzer/releases/tag/1.2.0)
### [1.2.0](https://github.com/kschweiger/track_analyzer/compare/1.1.2...1.2.0) (2024-01-28)

#### Code Refactoring

- **get_closest_point:** n_segment type hint and docstring reflects that full track can be used ([453d0dd](https://github.com/kschweiger/track_analyzer/commit/453d0dd77ee386f36671265c98ea406db872b2e5))
- cli tools are available via extra cli (#17) ([712e59c](https://github.com/kschweiger/track_analyzer/commit/712e59c42ccc32027387a87a05268ec2b3a9200b))

<a name="1.1.2"></a>

----------------------------

## [1.1.2](https://github.com/kschweiger/track_analyzer/releases/tag/1.1.2)
### [1.1.2](https://github.com/kschweiger/track_analyzer/compare/1.0.0...1.1.2) (2024-01-14)

#### Features

- Convert model dataclasses to pydantic models  (#16) ([488600b](https://github.com/kschweiger/track_analyzer/commit/488600b9e069a3a4234abb20d09469ea508629a9))
- enhance-elevation cli (#15) ([9318d93](https://github.com/kschweiger/track_analyzer/commit/9318d93612ad3aa01673c385a8d8cae36487d5d3))
- **visualize:** Adding function for plotting data of multiple tracks ([9b96054](https://github.com/kschweiger/track_analyzer/commit/9b96054e1fe5b75e682954e2db5de01ac1e6da06))


<a name="1.1.1"></a>

----------------------------

## [1.0.0](https://github.com/kschweiger/track_analyzer/releases/tag/1.0.0)
### [1.0.0](https://github.com/kschweiger/track_analyzer/compare/0.5.3...1.0.0) (2023-12-04)

Release of first non-development version of the package on PyPi 🎉

<a name="0.5.3"></a>

**Full Changelog**: https://github.com/kschweiger/track_analyzer/compare/0.5.3...1.0.0

----------------------------

## [0.5.1](https://github.com/kschweiger/track_analyzer/releases/tag/0.5.1)
### [0.5.1](https://github.com/kschweiger/track_analyzer/compare/0.5.0...0.5.1) (2023-12-03)

<a name="0.5.0"></a>

### [0.5.0](https://github.com/kschweiger/track_analyzer/compare/0.4.1...0.5.0) (2023-12-03)

#### Features

- Interpolation includes extentions heartrate, cadence, power (#13) ([e777fa1](https://github.com/kschweiger/track_analyzer/commit/e777fa1505b28fc3e626ecb0fdcaba23ebaa0231))
- **visualize.map:** Adding map_style and line_width for map plot functions ([0beaec2](https://github.com/kschweiger/track_analyzer/commit/0beaec264093dd03c11e3e755a9b70d7aa6dbcb1))
- **Track:** Adding split method (#11) ([3ac4a42](https://github.com/kschweiger/track_analyzer/commit/3ac4a427f2a46300c6aba56f58b44a6a5e953e51))
- **Track:** Added plot method (#9) ([d71b888](https://github.com/kschweiger/track_analyzer/commit/d71b88821ae48b6b6bf2348ddad8793ad21a5f74))

#### Bug Fixes

- **plot_segments_on_map:** Plot now works with tracks w/o time ([4789ddb](https://github.com/kschweiger/track_analyzer/commit/4789ddb300ceadd1907a9ab402a11a5068703581))
- Track DataFrame with multiple segments was missing datapoints ([975f1f9](https://github.com/kschweiger/track_analyzer/commit/975f1f9f5e695fe11cd1c38740692aa4282a62dd))

#### Code Refactoring

- Renamed package to geo-track-analyzer ([13779ef](https://github.com/kschweiger/track_analyzer/commit/13779eff5622d3351cb0143419adf7bf0e902acf))


----------------------------

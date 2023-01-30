##  (2023-01-30)




## <small>0.0.2 (2023-01-30)</small>

* Bump version: 0.0.1 → 0.0.2 ([75a94b3](https://github.com/kschweiger/track_analyzer/commit/75a94b3))
* feat(enhancer): Added enhancer factory; Renamed Exception; Added inplace option to enhance_track met ([47e6054](https://github.com/kschweiger/track_analyzer/commit/47e6054))
* feat(plot_track_2d): Added optional POIs to the plot; Color can be passed as arguement; Updated requ ([3679319](https://github.com/kschweiger/track_analyzer/commit/3679319))
* feat(PyTrack): Added a Track that is initialized with python objects for points, elevation and time ([2c27312](https://github.com/kschweiger/track_analyzer/commit/2c27312))
* feat(Track): Added linear interpolation method ([23f6d95](https://github.com/kschweiger/track_analyzer/commit/23f6d95))
* feat(Track): Added method for retrieving coordinates, elevations and times of the points in a segmen ([be38442](https://github.com/kschweiger/track_analyzer/commit/be38442))
* feat(Track): Added to_xml method ([10af4e9](https://github.com/kschweiger/track_analyzer/commit/10af4e9))
* refactor(OpenTopoElevationEnhancer): Added skip_checks argument ([194f5cb](https://github.com/kschweiger/track_analyzer/commit/194f5cb))
* refactor(Track): Changed default value of the moving in segment data w/o times ([9924113](https://github.com/kschweiger/track_analyzer/commit/9924113))
* refactor(Track): Setting cum_distance_moving equal to cum_distance as all points are considered movi ([fda1957](https://github.com/kschweiger/track_analyzer/commit/fda1957))
* doc: Updated CHANGELOG.md ([2666ae2](https://github.com/kschweiger/track_analyzer/commit/2666ae2))



##  (2022-09-09)




## <small>0.0.1 (2022-09-09)</small>

* Bump version: 0.0.0 → 0.0.1 ([bf6abe1](https://github.com/kschweiger/track_analyzer/commit/bf6abe1))
* Moved to setup.cfg+pyproject.toml ([6e94948](https://github.com/kschweiger/track_analyzer/commit/6e94948))
* chore: Added .gitignore and LICENSE ([2da0fc3](https://github.com/kschweiger/track_analyzer/commit/2da0fc3))
* chore: Added bump2version to dev.in ([d421cd4](https://github.com/kschweiger/track_analyzer/commit/d421cd4))
* chore: Added pytest to setup.cfg ([e5baa09](https://github.com/kschweiger/track_analyzer/commit/e5baa09))
* chore: Inital commit with basic files (setup, requirements, package directory) ([68f9de7](https://github.com/kschweiger/track_analyzer/commit/68f9de7))
* ci: Added GitHub actions for unit-tests ([04f11e8](https://github.com/kschweiger/track_analyzer/commit/04f11e8))
* feat: Added classes used to enhance tracks. This commit adds OpenElevationEnhancer that used an open ([5b5a740](https://github.com/kschweiger/track_analyzer/commit/5b5a740))
* feat: Added datacalsses and some basic utility functions ([7d4313e](https://github.com/kschweiger/track_analyzer/commit/7d4313e))
* feat: Added Elevation enhancer using OpenTopo api ([01d6139](https://github.com/kschweiger/track_analyzer/commit/01d6139))
* feat: Added main track analysis class ([a467e43](https://github.com/kschweiger/track_analyzer/commit/a467e43))
* feat: Added plotting functions ([486e4bd](https://github.com/kschweiger/track_analyzer/commit/486e4bd))
* feat: Added plotting track on open-street-map ([81c4ed2](https://github.com/kschweiger/track_analyzer/commit/81c4ed2))
* feat: Added script for approximate the center of a list of latitude, longitude pairs ([58fba8f](https://github.com/kschweiger/track_analyzer/commit/58fba8f))
* feat(ByteTrack): Added Track that loads from a byte object ([ff18914](https://github.com/kschweiger/track_analyzer/commit/ff18914))
* refactor: Moved tests ([14b447a](https://github.com/kschweiger/track_analyzer/commit/14b447a))
* refactor: Refactored _get_processed_data_for_segment to use a DataFrame ([9921d4a](https://github.com/kschweiger/track_analyzer/commit/9921d4a))
* refactor(visualize): Minor changes to plot2d ([a5d15ab](https://github.com/kschweiger/track_analyzer/commit/a5d15ab))
* feature(OpenTopoElevationEnhancer): Added api health and dataset checks ([99f13bb](https://github.com/kschweiger/track_analyzer/commit/99f13bb))
* fix: Addressed a Value error in the asin calculation ([2f49d19](https://github.com/kschweiger/track_analyzer/commit/2f49d19))




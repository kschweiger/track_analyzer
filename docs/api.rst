.. currentmodule:: geo_track_analyzer

API Reference
=============

.. _explanation_api:

Tracks
------
.. autosummary::
   :toctree: generated

   geo_track_analyzer.GPXFileTrack
   geo_track_analyzer.FITTrack
   geo_track_analyzer.PyTrack
   geo_track_analyzer.ByteTrack
   geo_track_analyzer.SegmentTrack

Model
-----
.. autosummary::
   :toctree: generated

    geo_track_analyzer.model.Position2D
    geo_track_analyzer.model.Position3D
    geo_track_analyzer.model.ElevationMetrics
    geo_track_analyzer.model.SegmentOverview
    geo_track_analyzer.model.SegmentOverlap
    geo_track_analyzer.model.PointDistance




Enhancer
--------
.. autosummary::
   :toctree: generated

    geo_track_analyzer.OpenTopoElevationEnhancer
    geo_track_analyzer.OpenElevationEnhancer
    geo_track_analyzer.get_enhancer



Visualizations
--------------
.. autosummary::
   :toctree: generated

    geo_track_analyzer.visualize.plot_track_3d
    geo_track_analyzer.visualize.plot_track_line_on_map
    geo_track_analyzer.visualize.plot_track_enriched_on_map
    geo_track_analyzer.visualize.plot_track_2d
    geo_track_analyzer.visualize.plot_track_with_slope
    geo_track_analyzer.visualize.plot_segments_on_map

Track comparisons
-----------------

.. autosummary::
   :toctree: generated

   geo_track_analyzer.compare.check_segment_bound_overlap
   geo_track_analyzer.compare.get_segment_overlap
   geo_track_analyzer.compare.convert_segment_to_plate
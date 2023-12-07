.. currentmodule:: geo_track_analyzer

Track enhancemnet
=================

The enhancer provided in this package aim to provide a common interface for enhancing
a Track with data.

Elevation enhancement
---------------------

Updating or adding elevation data to a ``Track`` can be accomplished by using the classes
implementing the ``ElevationEnhancer`` API.  This might be desirable for various reasons like:

- No elevation data was recorded
- The recorded elevation is data is inaccurate
- Elevation data should be synced between different Tracks

Currently two interfaces for web-based REST API's are supported:

- :class:`~geo_track_analyzer.OpenTopoElevationEnhancer`: Interface for OpenTopoData API (https://opentopodata.org)
- :class:`~geo_track_analyzer.OpenElevationEnhancer`: Interface for  OpenElevation API (https://open-elevation.com)

Depending on the API that should be used, settings are defined when initializing the object. See the
specific documentation of the relevant objects and API's. When using the public (free) API's set as default in
the objects, rate or similar restrictions may apply.

A enhancer can be used like this:

.. code-block:: python

    enhancer = ElevationEnhancer()

    my_track = GPXFileTrack(gpx_file="...")

    enhancer.enhance_track(track=my_track.track, inplace=True)

See `examples/enhance_elevation.py <https://github.com/kschweiger/track_analyzer/blob/main/examples/enhance_elevation.py>`_ for a more detailed example.

The author of this package recommends using a `self hosted OpenTopoData API via a docker containers <https://www.opentopodata.org/#host-your-own>`_ with a
`open source EU-DEM dataset <https://www.opentopodata.org/datasets/eudem/>`_ for europe.
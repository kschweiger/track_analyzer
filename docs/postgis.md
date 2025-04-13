# PostGIS integration

???+ note "Extra"

    Not all dependencies for the PostGIS integration are not installed by default. Please use the `postgis` extra during installation.

The package provides an (opinionated) interface to save/load tracks to/from a Postgres database using the PostGIS extension. The functions are located in the `geo_track_analyzer.postgis` module and operate on SQLAlchemy Engine that is passed into the functions.

## API Reference

::: geo_track_analyzer.postgis.create_tables
::: geo_track_analyzer.postgis.insert_track
::: geo_track_analyzer.postgis.load_track



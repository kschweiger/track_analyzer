import logging
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Any, Generator

from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

from geo_track_analyzer.exceptions import (
    DBTrackInitializationError,
    GPXPointExtensionError,
)
from geo_track_analyzer.track import PyTrack, Track
from geo_track_analyzer.utils.internal import get_extension_value

logger = logging.getLogger(__name__)


def create_tables(
    engine: Engine,
    schema: str,
    track_table: str,
    points_table: str,
    extensions: list[tuple[str, str]] | None = None,
) -> None:
    """
    Create the tables for the tracks and points using the passed Engine

    :param engine: SQLLalchemy Engine for the Postgres database
    :param schema: Name of the schema in the database
    :param track_table: Name of the table containing track information
    :param points_table: Name of the table containing the points of
        all tracks
    :param extensions: Extensions columns (tuple of name and type). If None
        is passed heartrate, cadence, power, and temperature are created
    """
    track_stmt = f"""
        CREATE TABLE IF NOT EXISTS {schema}.{track_table} (
            id SERIAL PRIMARY KEY,
            track_name TEXT,
            track_date DATE,
            source TEXT
        );
    """

    if extensions is None:
        extensions = [
            ("heartrate", "INTEGER"),
            ("cadence", "INTEGER"),
            ("power", "INTEGER"),
            ("temperature", "DOUBLE PRECISION"),
        ]

    points_stmt = f"""
        CREATE TABLE IF NOT EXISTS {schema}.{points_table} (
        id SERIAL PRIMARY KEY,
        track_id INTEGER REFERENCES {schema}.{track_table}(id),
        segment_id INTEGER NOT NULL,
        geom GEOGRAPHY(POINT, 4326),
        elevation DOUBLE PRECISION DEFAULT NULL,
        time TIMESTAMP WITH TIME ZONE,
        {",".join([f"{n} {t} DEFAULT NULL" for n, t in extensions])},
        -- Add other extension fields as needed
        CONSTRAINT fk_track FOREIGN KEY (track_id) REFERENCES {schema}.{track_table}(id)
    );
    """

    index_stmt = f"""
    CREATE INDEX {points_table}_geom_idx ON {schema}.{points_table} USING GIST (geom);
    """

    with engine.connect() as conn:
        logger.debug("Table %s.%s created", schema, track_table)
        conn.execute(text(track_stmt))
        conn.commit()
        logger.debug("Table %s.%s created", schema, points_table)
        conn.execute(text(points_stmt))
        conn.commit()
        logger.debug("Index created")
        conn.execute(text(index_stmt))
        conn.commit()


def get_track_data(
    track: Track, track_id: int, batch_size: int = 100
) -> Generator[
    list[dict[str, Any]],
    None,
    None,
]:
    """
    Generator function that yields batches of track data tuples.

    Args:
        track: Track object containing GPS data
        batch_size: Number of data points to include in each batch

    Yields:
        List of tuples containing track data in batches
    """
    current_batch = []
    for i, segment in enumerate(track.track.segments):
        for point in segment.points:
            long, lat, ele, time = (
                point.longitude,
                point.latitude,
                point.elevation,
                point.time,
            )
            ext = {}
            for key in ["heartrate", "cadence", "power", "temperature"]:
                try:
                    ext[key] = float(get_extension_value(point, key))
                except GPXPointExtensionError:
                    ext[key] = None
            _data = {
                "track_id": track_id,
                "segment_id": i,
                "lat": lat,
                "long": long,
                "time": time,
                "ele": ele,
            }
            _data.update(ext)

            current_batch.append(_data)
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []

    # Yield any remaining data points in the final batch
    if current_batch:
        yield current_batch


@lru_cache(maxsize=5)
def _find_extensions(conn: Connection, schema: str, table: str) -> list[str]:
    base_cols = [
        "id",
        "track_id",
        "segment_id",
        "geom",
        "elevation",
        "time",
    ]
    _columns = conn.execute(
        text(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = '{schema}' AND table_name = '{table}'
        """)
    ).fetchall()

    extensions = [r[0] for r in _columns if r[0] not in base_cols]
    logger.debug("Found extenstions %s in %s.%s", extensions, schema, table)
    return extensions


def insert_track(
    track: Track,
    engine: Engine,
    schema: str,
    track_table: str,
    points_table: str,
    source: str,
) -> int | None:
    """
    Insert a track into the database

    :param track: Track to be inserted
    :param engine: SQLLalchemy Engine for the Postgres database
    :param schema: Name of the schema in the database
    :param track_table: Name of the table containing track information
    :param points_table: Name of the table containing the points of
        all tracks
    :param source: Set a source of the track in the track table.

    :return: None if insertion failed and track_id if successfull
    """
    start_time = track.track.get_time_bounds().start_time

    with engine.connect() as conn:
        track_stmt = f"""
            INSERT INTO {schema}.{track_table} (track_name, track_date, source)
            VALUES (:name, :date, :source) RETURNING id
        """
        new_track_id = conn.execute(
            text(track_stmt),
            [
                {
                    "name": track.track.name,
                    "date": None if start_time is None else start_time.date(),
                    "source": source,
                }
            ],
        ).fetchone()
        conn.commit()
        logger.info("Track entry created")
        if new_track_id is None:
            logger.error("Track insertion uncessefull")
            return None
        new_track_id = new_track_id[0]
        logger.debug("Inserted track with id %s", new_track_id)
        extensions = _find_extensions(conn, schema, points_table)
        points_stmt = f"""
            INSERT INTO {schema}.{points_table}
            (track_id, segment_id, geom,
             elevation, time, {",".join(extensions)})
            VALUES (:track_id, :segment_id,
                    ST_SetSRID(ST_MakePoint(:long, :lat), 4326)::geography,
                    :ele, :time,{",".join(map(lambda v: f":{v}", extensions))})
        """
        for point_batch in get_track_data(track, new_track_id, 100):
            conn.execute(text(points_stmt), point_batch)
            conn.commit()
        logger.info("All points inserted")
        return new_track_id


def _load_points(
    conn: Connection, track_id: int, schema: str, table: str, extensions: list[str]
) -> dict[int, dict[str, list[str] | list[float | None] | list[datetime | None]]]:
    ret_data = {}
    segment_stmt = (
        f"SELECT DISTINCT segment_id FROM {schema}.{table} WHERE track_id = {track_id}"
    )
    segment_ids = list([r[0] for r in conn.execute(text(segment_stmt)).fetchall()])
    if not segment_ids:
        raise DBTrackInitializationError(
            "Could not load any segments for track id %s" % track_id
        )
    for segment_id in segment_ids:
        stmt = f"""
            SELECT
                ST_Y(geom::geometry) AS latitude,
                ST_X(geom::geometry) AS longitude,
                elevation,
                time,
                {",".join(extensions)}
            FROM {schema}.{table}
            WHERE track_id = {track_id} AND
                  segment_id = {segment_id}
        """
        data = conn.execute(text(stmt)).fetchall()
        if not data:
            raise DBTrackInitializationError(
                "Could not load points for segment %s in track %s"
                % (segment_id, track_id)
            )
        segment_data = defaultdict(list)
        for d in data:
            for key, value in d._mapping.items():
                segment_data[key].append(value)
        ret_data[segment_id] = segment_data

    return ret_data


def load_track(
    track_id: int,
    engine: Engine,
    schema: str,
    track_table: str,
    points_table: str,
    **track_kwargs,
) -> Track:
    """
    Insert a track into the database

    :param track_id: id of the track in the database
    :param engine: SQLLalchemy Engine for the Postgres database
    :param schema: Name of the schema in the database
    :param track_table: Name of the table containing track information
    :param points_table: Name of the table containing the points of
        all tracks
    :param track_kwargs: Additional keyword arguments passed to the Track.

    :return: Track Object.
    """
    track_stmt = f"SELECT * FROM {schema}.{track_table} WHERE id = {track_id}"
    track = None
    with engine.connect() as conn:
        logger.debug("Loading track: %s from %s.%s", track_id, schema, track_table)
        _track_data = conn.execute(text(track_stmt)).fetchone()
        if _track_data is None:
            raise DBTrackInitializationError(
                "No track with id %s in %s.%s" % (track_id, schema, track_table)
            )
        track_data = _track_data._mapping

        logger.debug("Loading points from %s.%s", schema, points_table)
        extensions = _find_extensions(conn, schema, points_table)
        segments = _load_points(conn, track_id, schema, points_table, extensions)
        for i, segment_id in enumerate(sorted(segments.keys())):
            segment_data = segments[segment_id]
            extension_data = {}
            for extension in extensions:
                extension_data[extension] = segment_data[extension]
            _data = dict(
                points=list(zip(segment_data["latitude"], segment_data["longitude"])),
                elevations=segment_data["elevation"],
                times=segment_data["time"],
                extensions=extension_data,
            )
            if i == 0:
                track = PyTrack(
                    **_data,
                    **track_kwargs,
                )
            else:
                assert track is not None
                track.add_segmeent(**_data)  # type: ignore
    assert track is not None
    track.track.name = track_data["track_name"]
    return track

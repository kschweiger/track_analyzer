import os
import uuid
from typing import Generator

import pytest
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text

from geo_track_analyzer.exceptions import DBTrackInitializationError
from geo_track_analyzer.postgis.db import (
    _find_extensions,
    create_tables,
    get_track_data,
    insert_track,
    load_track,
)
from geo_track_analyzer.track import PyTrack, Track

SCHEMA_NAME = f"test_gta_{str(uuid.uuid4()).replace('-', '_')}"


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    load_dotenv()
    db_user = os.environ["DB_USER"]
    db_password = os.environ["DB_PASSWORD"]
    db_host = os.environ["DB_HOST"]
    db_port = os.environ["DB_PORT"]
    db_database = os.environ["DB_DATABASE"]
    _engine = create_engine(
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
    )

    with _engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
        conn.commit()
    yield _engine

    with _engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA {SCHEMA_NAME} CASCADE"))
        conn.commit()


@pytest.mark.parametrize(
    ("extensions", "exp_extension_cols"),
    [
        (None, ["heartrate", "cadence", "power", "temperature"]),
        ([("some_ext", "INTEGER")], ["some_ext"]),
    ],
)
def test_create_tables(
    engine: Engine,
    extensions: list[tuple[str, str]] | None,
    exp_extension_cols: list[str],
) -> None:
    table_name_postfix = str(uuid.uuid4()).replace("-", "_")
    track_table = f"tracks_{table_name_postfix}"
    points_table = f"points_{table_name_postfix}"
    create_tables(
        engine,
        SCHEMA_NAME,
        track_table,
        points_table,
        extensions,
    )

    with engine.connect() as conn:
        tables = conn.execute(
            text(f"select tablename from pg_tables where schemaname='{SCHEMA_NAME}'")
        ).fetchall()

        tables = [r[0] for r in tables]
        assert track_table in tables
        assert points_table in tables

        assert sorted(_find_extensions(conn, SCHEMA_NAME, points_table)) == sorted(
            exp_extension_cols
        )


def test_insert_track(
    track_for_test: Track,
    engine: Engine,
) -> None:
    table_name_postfix = "test_insert_track"
    track_table = f"{table_name_postfix}_tracks"
    points_table = f"{table_name_postfix}_points"
    create_tables(
        engine,
        SCHEMA_NAME,
        track_table,
        points_table,
    )

    assert (
        insert_track(
            track_for_test,
            engine,
            SCHEMA_NAME,
            track_table,
            points_table,
            source="test",
        )
        == 1
    )


def test_insert_and_load_track(
    track_for_test: Track,
    engine: Engine,
) -> None:
    table_name_postfix = "test_insert_and_load_track"
    track_table = f"{table_name_postfix}_tracks"
    points_table = f"{table_name_postfix}_points"
    create_tables(
        engine,
        SCHEMA_NAME,
        track_table,
        points_table,
    )

    assert (
        insert_track(
            track_for_test,
            engine,
            SCHEMA_NAME,
            track_table,
            points_table,
            source="test",
        )
        == 1
    )

    loaded_track = load_track(1, engine, SCHEMA_NAME, track_table, points_table)

    assert len(track_for_test.track.segments) == 2
    assert len(loaded_track.track.segments) == len(track_for_test.track.segments)
    for i in range(2):
        assert len(loaded_track.track.segments[i].points) == len(
            track_for_test.track.segments[i].points
        )


def test_load_track_error(engine: Engine) -> None:
    table_name_postfix = "test_load_track_error"
    track_table = f"{table_name_postfix}_tracks"
    points_table = f"{table_name_postfix}_points"
    create_tables(
        engine,
        SCHEMA_NAME,
        track_table,
        points_table,
    )

    with pytest.raises(DBTrackInitializationError):
        load_track(42, engine, SCHEMA_NAME, track_table, points_table)


def test_get_track_data() -> None:
    track = PyTrack(
        points=[(i, i) for i in range(6)],
        elevations=[i * 100 for i in range(6)],
        times=None,
    )

    _data = get_track_data(track, 1, 5)
    assert len(next(_data)) == 5

    assert len(next(_data)) == 1

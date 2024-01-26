from pathlib import Path, PosixPath
from typing import Type

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from geo_track_analyzer.cli._update_elevation import convert_kwargs
from geo_track_analyzer.cli._update_elevation import main as update_elevation
from geo_track_analyzer.enhancer import ElevationEnhancer
from geo_track_analyzer.track import GPXFileTrack, PyTrack


def test_update_elevation_convert_kwargs() -> None:
    res = convert_kwargs(("AAA=XXX", "BBB=True", "CCC=False", "DDD=true", "EEE=false"))

    assert res["AAA"] == "XXX"
    assert isinstance(res["BBB"], bool)
    assert res["BBB"]
    assert isinstance(res["DDD"], bool)
    assert res["DDD"]
    assert isinstance(res["CCC"], bool)
    assert not res["CCC"]
    assert isinstance(res["EEE"], bool)
    assert not res["EEE"]


def test_update_elevation_fail_no_args() -> None:
    runner = CliRunner()
    result = runner.invoke(update_elevation, [])

    assert result.exit_code == 2


def test_update_elevation_fail_no_gpx(tmp_path: PosixPath) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with open("hello.txt", "w") as f:
            f.write("Hello World!")

        result = runner.invoke(
            update_elevation,
            [
                "hello.txt",
                "--enhancer",
                "OpenTopoElevation",
                "--url",
                "http://localhost:1234",
            ],
        )

        assert result.exit_code == 2


@pytest.mark.parametrize("raw_args", [["aaa"], ["aaa=xy="]])
def test_update_elevation_fail_raw_arg_conversion(
    tmp_path: PosixPath, raw_args: list[str]
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with open("hello.gpx", "w") as f:
            f.write("Does not matter for this test")

        result = runner.invoke(
            update_elevation,
            [
                "hello.gpx",
                "--enhancer",
                "OpenTopoElevation",
                "--url",
                "http://localhost:1234",
            ]
            + raw_args,
        )

        assert result.exit_code == 2


def test_update_elevation_succ(
    mocker: MockerFixture,
    tmp_path: PosixPath,
    mock_elevation_enhancer: Type[ElevationEnhancer],
) -> None:
    mocker.patch(
        "geo_track_analyzer.cli._update_elevation.get_enhancer",
        return_value=mock_elevation_enhancer,
    )

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        track = PyTrack(
            points=[(47.99609, 7.849401), (47.99610, 7.849402), (47.99611, 7.849403)],
            elevations=None,
            times=None,
        )
        assert not track.track.has_elevations()
        with open("test_track.gpx", "w") as f:
            f.write(track.get_xml())

        result = runner.invoke(
            update_elevation,
            [
                "test_track.gpx",
                "--enhancer",
                "OpenTopoElevation",
                "--url",
                "http://localhost:1234",
            ],
        )

        assert result.exit_code == 0

        assert Path("test_track_enhanced_elevation.gpx").is_file()

        enhanced_track = GPXFileTrack("test_track_enhanced_elevation.gpx")
        assert enhanced_track.track.has_elevations()

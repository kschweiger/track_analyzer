import pandas as pd
import pytest

from geo_track_analyzer.visualize.utils import group_dataframe


def test_group_dataframe_composiiton() -> None:
    data = pd.DataFrame(
        {
            "x": range(0, 10),
            "y": range(0, 10),
            "c": 5 * ["A"] + 5 * ["B"],
        }
    )

    frames = group_dataframe(data, "c", 1)

    assert len(frames) == 2
    assert len(frames[0]) == 5
    assert len(frames[1]) == 6
    assert frames[0]["y"].to_list() == [0, 1, 2, 3, 4]
    assert frames[1]["y"].to_list() == [4, 5, 6, 7, 8, 9]


@pytest.mark.parametrize(
    ("data", "min_in_group", "n_frames_exp", "exp_lens", "exp_col_values"),
    [
        (
            pd.DataFrame(
                {
                    "x": range(0, 20),
                    "y": [v / 2 for v in range(0, 20)],
                    "c": 5 * ["A"] + 7 * ["B"] + 3 * ["A"] + 5 * ["C"],
                }
            ),
            1,
            4,
            [5, 8, 4, 6],
            ["A", "B", "A", "C"],
        ),
        (
            pd.DataFrame(
                {
                    "x": range(0, 20),
                    "y": [v / 2 for v in range(0, 20)],
                    "c": 5 * ["A"] + 7 * ["B"] + 3 * ["A"] + 5 * ["C"],
                }
            ),
            3,
            3,
            [5, 11, 6],
            ["A", "B", "C"],
        ),
        (
            pd.DataFrame(
                {
                    "x": range(0, 20),
                    "y": [v / 2 for v in range(0, 20)],
                    "c": 5 * ["A"] + 7 * ["B"] + 3 * ["A"] + 5 * ["B"],
                }
            ),
            3,
            2,
            [5, 16],
            ["A", "B"],
        ),
    ],
)
def test_group_dataframe(
    data: pd.DataFrame,
    min_in_group: int,
    n_frames_exp: int,
    exp_lens: list[int],
    exp_col_values: list[str],
) -> None:
    # Check test setup
    assert len(exp_lens) == n_frames_exp
    assert len(exp_col_values) == n_frames_exp
    cols_pre = set(data.columns)

    frames = group_dataframe(data, "c", min_in_group)

    assert cols_pre == set(data.columns)
    assert isinstance(frames, list)
    assert len(frames) == n_frames_exp
    for f, exp_len, exp_name in zip(frames, exp_lens, exp_col_values):
        assert len(f) == exp_len
        assert set(f["c"].unique()) == {exp_name}


def test_group_dataframe_with_colors() -> None:
    df = pd.DataFrame(
        {
            "x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "y": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            "z": ["A", "A", "A", "B", "B", "C", "D", "D", "D", "D"],
            "z_colors": ["CA", "CA", "CA", "CB", "CB", "CC", "CD", "CD", "CD", "CD"],
        }
    )

    groups = group_dataframe(df, "z", 3)

    assert len(groups) == 2

    colors_0 = groups[0]["z_colors"].unique()
    assert len(colors_0) == 1
    assert colors_0[0] == "CA"

    colors_1 = groups[1]["z_colors"].unique()
    assert len(colors_1) == 1
    assert colors_1[0] == "CD"

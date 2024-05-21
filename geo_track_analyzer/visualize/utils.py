import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def hex_to_rgb(hex: str) -> tuple[int, int, int]:
    """
    Pass a hex color name (as string) and get the RGB value

    Source: https://medium.com/@BrendanArtley/matplotlib-color-gradients-21374910584b

    >> hex_to_RGB("#FFFFFF") -> [255,255,255]
    """
    return tuple([int(hex[i : i + 2], 16) for i in range(1, 6, 2)])  # type: ignore


def get_color_gradient(c1: str, c2: str, n: int) -> list[str]:
    """
    Create a color gradient between two passed colors with N steps.

    Source: https://medium.com/@BrendanArtley/matplotlib-color-gradients-21374910584b
    """
    assert n > 1
    c1_rgb = np.array(hex_to_rgb(c1)) / 255
    c2_rgb = np.array(hex_to_rgb(c2)) / 255
    mix_pcts = [x / (n - 1) for x in range(n)]
    rgb_colors = [((1 - mix) * c1_rgb + (mix * c2_rgb)) for mix in mix_pcts]
    return [
        ("#" + "".join([format(int(round(val * 255)), "02x") for val in item])).upper()
        for item in rgb_colors
    ]


def get_slope_colors(
    color_min: str,
    color_neutral: str,
    color_max: str,
    min_slope: int = -16,
    max_slope: int = 16,
) -> Dict[int, str]:
    """
    Generate a color gradient for the slope plots. The three passed colors are
    used for the MIN_SLOPE point, the 0 point and the MAX_SLOPE value respectively


    :param color_min: Color at the MIN_SLOPE value
    :param color_neutral: Color at 0
    :param color_max: Color at the MAX_SLOPE value
    :param min_slope: Minimum slope of the gradient, defaults to -16
    :param max_slope: Maximum slope of the gradient, defaults to 16
    :return: Dict mapping between slopes and colors
    """
    neg_points = list(range(min_slope, 1))
    pos_points = list(range(0, max_slope + 1))
    neg_colors = get_color_gradient(color_min, color_neutral, len(neg_points))
    pos_colors = get_color_gradient(color_neutral, color_max, len(pos_points))
    colors = {}
    colors.update({point: color for point, color in zip(neg_points, neg_colors)})
    colors.update({point: color for point, color in zip(pos_points, pos_colors)})
    return colors


def group_dataframe(
    data: pd.DataFrame, group_by: str, min_in_group: int
) -> list[pd.DataFrame]:
    """
    Group the DataFrame by a specified column, ensuring that each group contains at
    least a minimum number of rows. Except the first group, the last value from the
    previous group is prepended to the group to get consitent lines in a plot. Small
    groups (defined by min_in_group) will be merged in previous group. If this leads
    to multiple groups with same name, these will also be merged.

    :param data: The DataFrame to be grouped.
    :param group_by: The name of the column to group by.
    :param min_in_group: The minimum number of rows required in each group. Will be
        merged with previous group if number is not reached

    :return: A list of DataFrames, each containing a group of rows
        from the original DataFrame.
    """
    frames: list[pd.DataFrame] = []
    data["group"] = (data[group_by] != data[group_by].shift()).cumsum()
    group_by_color = f"{group_by}_colors".replace("zones", "zone")
    for _, group in data.groupby("group"):
        # First is always just added to the list
        if len(frames) == 0:
            frames.append(group)
            continue

        color = None

        if len(group) > min_in_group:
            group_name = group[group_by].unique()[0]
            if group_by_color in group:
                color = group[group_by_color].unique()[0]

            tral_prev_group = frames[len(frames) - 1].tail(1).copy()
            group = pd.concat([tral_prev_group, group])
            # Make sure the last entry from previous group hast same name
            group[group_by] = group_name
            if color is not None:
                group[group_by_color] = color
        else:
            group_name = frames[len(frames) - 1][group_by].unique()[0]
            if group_by_color in group:
                color = frames[len(frames) - 1][group_by_color].unique()[0]

            frames[len(frames) - 1] = pd.concat([frames[len(frames) - 1], group])
            frames[len(frames) - 1][group_by] = group_name
            if color is not None:
                frames[len(frames) - 1][group_by_color] = color
            continue

        name = group[group_by].unique()[0]
        prev_name = frames[len(frames) - 1][group_by].unique()[0]
        if name != prev_name:
            frames.append(group)
        else:
            # THis only happends with merged groups in between so groups with same name
            # so we need to drop the duplicates
            frames[len(frames) - 1] = pd.concat(
                [frames[len(frames) - 1], group]
            ).drop_duplicates()

    # Cleanup
    data.drop("group", axis=1, inplace=True)  # noqa: PD002
    return frames

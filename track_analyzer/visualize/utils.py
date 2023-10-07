import logging
from typing import Dict

from track_analyzer.utils import get_color_gradient

logger = logging.getLogger(__name__)


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

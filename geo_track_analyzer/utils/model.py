import numpy as np
import numpy.typing as npt

from geo_track_analyzer.model import Zones


def format_zones_for_digitize(
    zones: Zones,
) -> tuple[npt.NDArray, list[str], None | list[str]]:
    vals = [-np.inf]
    if zones.intervals[0].name is None:
        names = [f"Zone 1 [0, {zones.intervals[0].end}]"]
    else:
        names = [f"{zones.intervals[0].name} [0, {zones.intervals[0].end}]"]
    if zones.intervals[0].color is None:
        colors = []
    else:
        colors = [zones.intervals[0].color]
    for i, interval in enumerate(zones.intervals[1:]):
        vals.append(float(interval.start))  # type: ignore
        base_name = f"Zone {i+2}" if interval.name is None else interval.name
        if interval.end is None:
            interval_str = f"[{interval.start}, \u221e]"
        else:
            interval_str = f"[{interval.start}, {interval.end}]"
        names.append(f"{base_name} {interval_str}")
        if interval.color is not None:
            colors.append(interval.color)
    vals.append(np.inf)

    _colors = None
    if len(colors) == len(names):
        _colors = colors

    return np.array(vals), names, _colors

import numpy as np
import numpy.typing as npt

from geo_track_analyzer.model import Zones


def format_zones_for_digitize(zones: Zones) -> tuple[npt.NDArray, list[str]]:
    vals = [-np.inf]
    if zones.intervals[0].name is None:
        names = ["Zone 1"]
    else:
        names = [zones.intervals[0].name]
    for i, interval in enumerate(zones.intervals[1:]):
        vals.append(float(interval.start))  # type: ignore
        names.append(f"Zone {i+2}" if interval.name is None else interval.name)
    vals.append(np.inf)

    return np.array(vals), names

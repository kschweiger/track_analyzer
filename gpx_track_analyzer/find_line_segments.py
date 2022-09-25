from copy import deepcopy
from dataclasses import dataclass
from math import pi, tan
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from gpx_track_analyzer.enums import SegmentCharacter


@dataclass
class StepResult:
    score: float
    slope: float
    length: float
    idx: Tuple[int, int]
    params: Tuple[float, float]


@dataclass
class MergedStepResult(StepResult):
    mean_slope: float
    character: SegmentCharacter
    merged_results: List[StepResult]


class IterationResult:
    def __init__(self, delay_iterations: int, max_iteration_length: int):
        """
        Object containing the information of all steps in  one iteration of the
        algorithm

        Args:
            delay_iterations: Delay in iteration steps which determines how long points
                              will be added to the iteration before the iteration is
                              stopped.
        """
        self.step_results: List[StepResult] = []
        self.min_score_iteration: int = -1

        self.iterations: int = 0

        self.delay_iterations: int = delay_iterations
        self.max_iteration_length = max_iteration_length

    def add_iteration(
        self,
        score: float,
        length: float,
        start_idx: int,
        end_idx: int,
        params: Tuple[float, float],
        slope: float,
    ) -> bool:
        """
        Add the info of the iteration to the object

        Args:
            score: Score parametrizing how well the function in this iteration fits the
                   points
            length: Lengths up to (and including) this iteration step
            start_idx: First index of the data considered for this iteration
            end_idx: Last index of the data considered for this iteration
            params: Parameters of function (here: a and b in y = a * x + b
            slope: Slope of the function in degree

        Returns:
            A boolean flag if the iteration should be stopped after this step
        """
        self.step_results.append(
            StepResult(
                score=score,
                slope=slope,
                length=length,
                idx=(start_idx, end_idx),
                params=params,
            )
        )

        if self.step_results and score <= min([s.score for s in self.step_results]):
            self.min_score_iteration = self.iterations
            self.iterations += 1
            return True
        else:
            iterations_from_min = self.iterations - self.min_score_iteration

            self.iterations += 1
            if iterations_from_min >= min(
                self.delay_iterations,
                self.max_iteration_length - self.min_score_iteration,
            ):
                return False
            else:
                return True

    def get_min_iteration(self) -> StepResult:
        """Return the step with the minimum score"""
        return self.step_results[self.min_score_iteration]

    def get_last_iteration(self) -> StepResult:
        """Return the last step in the iteration"""
        return self.step_results[-1]


def calc_diff_to_line(
    vals: List[Tuple[float, float]], idx_1: int, idx_2: int
) -> Tuple[List[Optional[float]], List[float], Tuple[float, float]]:
    """
    Use the x,y poirs in index idx_1 and idx_2 to estimate a line (y' = a * x + b) and
    calculate the difference for each point in vals to this line

    Args:
        vals: List of (x,y) pairs
        idx_1: First index used for estimating the line
        idx_2: Last index used for estimating the line

    Returns:
        List of y' - y differences, List of y', and (a,b)
    """
    try:
        a = (vals[idx_2][1] - vals[idx_1][1]) / (vals[idx_2][0] - vals[idx_1][0])
    except ZeroDivisionError:
        a = 0
    b = vals[idx_1][1] - (a * vals[idx_1][0])
    diffs: List[Optional[float]] = []
    line: List[float] = []
    for idx in range(len(vals)):

        y_prime = (a * vals[idx][0]) + b
        line.append(y_prime)
        if idx == idx_1 or idx == idx_2:
            diffs.append(None)
        else:
            diffs.append(y_prime - vals[idx][1])

    return diffs, line, (a, b)


def calc_line_score(
    values_true: List[float], values_exp: List[float], error: float
) -> float:
    """
    Calculate the score of the line with a chi^2 criterion
    TODO: I think we might need to add n_dof here

    Args:
        values_true: y values
        values_exp:  y' values
        error:  Error

    Returns:
        chi^2 score
    """
    score = 0
    for val_true, val_exp in zip(values_true, values_exp):
        score += pow(val_true - val_exp, 2) / pow(error, 2)

    return score


def merge_step_result(segments: List[StepResult]) -> StepResult:
    min_segment = deepcopy(sorted(segments, key=lambda r: r.score / r.length)[0])
    new_idx_start, _ = segments[0].idx
    _, new_idx_end = segments[-1].idx

    min_segment.idx = (new_idx_start, new_idx_end)
    return min_segment


def merge_merged_step_result(
    segments: List[MergedStepResult],
    data: pd.DataFrame,
    x: str,
    y: str,
    flat_threshold: float,
) -> MergedStepResult:
    new_idx_start, _ = segments[0].idx
    _, new_idx_end = segments[-1].idx

    merged_results = []
    sum_slope = 0
    for segment in segments:
        sum_slope += segment.mean_slope
        merged_results.extend(segment.merged_results)

    values = [(r[x], r[y]) for r in data.to_dict("records")]
    x_values = [v[0] for v in values]
    true_vals = [v[1] for v in values]

    diff, line, (a, b) = calc_diff_to_line(values, new_idx_start, new_idx_end)
    chi2_score = calc_line_score(
        true_vals[new_idx_start:new_idx_end],
        line[new_idx_start:new_idx_end],
        1,
    )
    slope = tan((line[-1] - line[0]) / (x_values[-1] - x_values[0])) * (180 / pi)
    if abs(slope) < flat_threshold:
        character = SegmentCharacter.FLAT
    else:
        character = SegmentCharacter.ASCENT if slope > 0 else SegmentCharacter.DECENT
    return MergedStepResult(
        mean_slope=sum_slope / len(segments),
        length=data[x].iloc[new_idx_end] - data[x].iloc[new_idx_start],
        idx=(new_idx_start, new_idx_end),
        merged_results=merged_results,
        slope=slope,
        score=chi2_score,
        params=(a, b),
        character=character,
    )


def find_line_segments(
    data: pd.DataFrame,
    x: str,
    y: str,
    delay: int = 2,
    merge_slope_tolerance: Optional[float] = 0.5,
    reeval_last_step: bool = True,
) -> List[StepResult]:
    """

    Args:
        data: Data used for the algorithm.
        x: DataFrame column used for the x values.
        y: DataFrame column used for the y values.
        delay: Delay in steps used to determine when an iteration should be stopped
        merge_slope_tolerance: Slope delta in degrees within which segments will be
                               merged. If None, no merging will be done.
        reeval_last_step: Flag determining if the last step should be reevaluated.
                          Additional setup counteracting delay setting dependent issues
                          in the last segment. See comment at the relevant if-clause
                          for more details.

    Returns:
        List of Line segments
    """
    values = [(r[x], r[y]) for r in data.to_dict("records")]

    start_idx = 0
    continue_search = True
    results = []
    line_params = []
    x_values = [v[0] for v in values]
    true_vals = [v[1] for v in values]
    # While loop for fining the segments. Also called an iteration
    while continue_search:
        length = 0
        end_points = range(start_idx + 2, len(values))
        iteration_results = IterationResult(
            delay_iterations=delay, max_iteration_length=len(end_points)
        )
        # For loop over the steps inside an iteration
        for end_idx in end_points:
            diff, line, (a, b) = calc_diff_to_line(values, start_idx, end_idx)
            chi2_score = calc_line_score(
                true_vals[start_idx:end_idx], line[start_idx:end_idx], 1
            )
            length += x_values[end_idx] - x_values[start_idx]
            slope = tan((line[-1] - line[0]) / (x_values[-1] - x_values[0])) * (
                180 / pi
            )
            keep_iterating = iteration_results.add_iteration(
                score=chi2_score,
                slope=slope,
                length=length,
                start_idx=start_idx,
                end_idx=end_idx,
                params=(a, b),
            )

            if not keep_iterating:
                line_result = iteration_results.get_min_iteration()
                results.append(line_result)
                line_params.append(line_result.params)
                _, min_end_idx = line_result.idx
                start_idx = min_end_idx
                break
            if keep_iterating and end_idx == (len(values) - 1):
                continue_search = False
                results.append(iteration_results.get_last_iteration())
                line_params.append((a, b))
    if reeval_last_step:
        # Depending on the delay set, the last segment might contain too many points
        # and should have been split into additional segment. To counteract this, run
        # the segmentation again on the last segment alone with a smaller delay and no
        # merging
        last_step = results.pop()
        ls_start, ls_end = last_step.idx
        last_step_results = find_line_segments(
            data[ls_start:ls_end],
            x=x,
            y=y,
            delay=2,
            merge_slope_tolerance=None,
            reeval_last_step=False,
        )
        # The returned StepResult now have the wrong indices so we need to update them
        # again to the one form the original dataset
        for res in last_step_results:
            idx_1, idx_2 = res.idx
            res.idx = (idx_1 + ls_start, idx_2 + ls_start)
            results.append(res)
        # Make sure the last segment end with the same index as the original one.
        s, _ = results[-1].idx
        results[-1].idx = (s, ls_end)

    # Clean the results
    # Merge consecutive lines with very close slopes

    if merge_slope_tolerance is None:
        return results
    else:
        results_ = []
        reference_slope = results[0].slope
        merged_segments = []
        for res in results:
            if (
                (reference_slope - merge_slope_tolerance)
                < res.slope
                <= (reference_slope + merge_slope_tolerance)
            ):
                merged_segments.append(res)
            else:
                results_.append(merge_step_result(merged_segments))
                reference_slope = res.slope
                merged_segments = [res]

        if merged_segments:
            results_.append(merge_step_result(merged_segments))

        return results_


if __name__ == "__main__":

    def calc_line(values, a, b):
        line_vals = []
        for val, _ in values:
            line_vals.append((a * val) + b)

        return line_vals

    values = [
        (0, 100),
        (20, 110),
        (40, 100),
        (60, 120),
        (80, 130),
        (100, 140),
        (120, 160),
        (140, 145),
        (160, 125),
        (180, 110),
        (200, 100),
    ]
    # values = [
    #     (0, 100),
    #     (20, 120),
    #     (40, 110),
    #     (60, 130),
    #     (80, 120),
    #     (100, 140),
    #     (120, 160),
    #     (140, 200),
    #     (160, 220),
    #     (180, 230),
    #     (200, 235),
    #     (220, 225),
    #     (240, 230),
    #     (260, 220),
    # ]
    data = pd.DataFrame(data=values, columns=["x", "y"])
    # manual_test(values)
    results = find_line_segments(data, x="x", y="y")

    plt.plot([v[0] for v in values], [v[1] for v in values], "x")
    for res in results:
        a, b = res.params
        line = calc_line(values, a, b)
        plt.plot([v[0] for v in values], line)
    plt.show()

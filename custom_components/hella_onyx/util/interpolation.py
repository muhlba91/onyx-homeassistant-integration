"""The ONYX interpolation utils."""

from math import ceil


def interpolate(
    current_value: int,
    target_value: int,
    duration: float,
    current_time: float,
    start_time: float,
) -> int:
    """Interpolates to the current value.

    The elapsed time is clamped to the animation, so the result never leaves the
    range between the current and the target value.
    """
    delta = min(max(current_time - start_time, 0), duration)
    delta_per_unit = (target_value - current_value) / duration
    return ceil(current_value + delta_per_unit * delta)

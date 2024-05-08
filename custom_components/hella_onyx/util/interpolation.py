"""The ONYX interpolation utils."""

from math import ceil


def interpolate(
    current_value: int,
    target_value: int,
    duration: float,
    current_time: float,
    start_time: float,
) -> int:
    """Interpolates to the current value."""
    delta = current_time - start_time
    delta_per_unit = (target_value - current_value) / duration
    return ceil(current_value + delta_per_unit * delta)

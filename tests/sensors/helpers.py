"""Helpers for the ONYX entity tests."""

from unittest.mock import AsyncMock, MagicMock

from onyx_client.data.animation_keyframe import AnimationKeyframe
from onyx_client.data.animation_value import AnimationValue
from onyx_client.data.numeric_value import NumericValue

from custom_components.hella_onyx.configuration import Configuration
from custom_components.hella_onyx.const import (
    DEFAULT_CLOSED_TOLERANCE,
    DEFAULT_MAX_DIM_DURATION,
    DEFAULT_MIN_DIM_DURATION,
    DEFAULT_MOVING_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
)

NOW = 1000.0


def make_api(additional_delay: int = 1000, interpolation_frequency: int = 5):
    """An API connector mock at the time NOW."""
    api = MagicMock()
    api.config = Configuration(
        DEFAULT_SCAN_INTERVAL,
        DEFAULT_MIN_DIM_DURATION,
        DEFAULT_MAX_DIM_DURATION,
        additional_delay,
        interpolation_frequency,
        DEFAULT_CLOSED_TOLERANCE,
        DEFAULT_MOVING_TIMEOUT,
        "finger",
        "token",
        None,
    )
    api.now.return_value = NOW
    api.send_device_command_action = AsyncMock()
    api.send_device_command_properties = AsyncMock()
    return api


def value(current: int, maximum: int = 100) -> NumericValue:
    """A value without animation."""
    return NumericValue(current, 0, maximum, False)


def animated(
    start_value: int,
    end_value: int,
    start: float,
    duration: float,
    maximum: int = 100,
    delay: float = 0,
) -> NumericValue:
    """A value animated from start_value to end_value; the value stays stale."""
    return NumericValue(
        start_value,
        0,
        maximum,
        False,
        AnimationValue(
            start, start_value, [AnimationKeyframe(end_value, duration, delay)]
        ),
    )

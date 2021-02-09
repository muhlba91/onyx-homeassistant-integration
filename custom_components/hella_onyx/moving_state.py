from enum import Enum, auto


class MovingState(Enum):
    """State if the shutter is moving or not."""

    STILL = auto()
    OPENING = auto()
    CLOSING = auto()

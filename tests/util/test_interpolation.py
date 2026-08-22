"""Test for the ONYX Interpolation util."""

from custom_components.hella_onyx.util.interpolation import interpolate


class TestInterpolation:
    def test_interpolate(self):
        assert interpolate(0, 50, 20000, 10000, 0) == 25

    def test_interpolate_decreasing(self):
        assert interpolate(50, 0, 20000, 10000, 0) == 25
        assert interpolate(100, 20, 10, 5, 0) == 60

    def test_interpolate_start_time_late(self):
        assert interpolate(0, 50, 20000, 10000, 20000) == -25

    def test_interpolate_current_time_after_duration(self):
        assert interpolate(0, 50, 20000, 30000, 0) == 75

"""Test for the ONYX Interpolation util."""
from custom_components.hella_onyx.util.interpolation import interpolate


class TestInterpolation:
    def test_interpolate(self):
        assert interpolate(0, 50, 20000, 10000, 0) == 25

    def test_interpolate_start_time_late(self):
        assert interpolate(0, 50, 20000, 10000, 20000) == -25

    def test_interpolate_current_time_after_duration(self):
        assert interpolate(0, 50, 20000, 30000, 0) == 75

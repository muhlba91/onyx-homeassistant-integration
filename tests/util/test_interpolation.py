"""Test for the ONYX Interpolation util."""

from custom_components.hella_onyx.util.interpolation import interpolate


class TestInterpolation:
    def test_interpolate(self):
        assert interpolate(0, 50, 20000, 10000, 0) == 25

    def test_interpolate_decreasing(self):
        assert interpolate(50, 0, 20000, 10000, 0) == 25
        assert interpolate(100, 20, 10, 5, 0) == 60

    def test_interpolate_before_start(self):
        assert interpolate(0, 50, 20000, 10000, 20000) == 0
        assert interpolate(50, 0, 20000, 10000, 20000) == 50

    def test_interpolate_at_start(self):
        assert interpolate(0, 90, 1.5, 0, 0) == 0

    def test_interpolate_at_end(self):
        assert interpolate(0, 90, 1.5, 1.5, 0) == 90
        assert interpolate(90, 0, 1.5, 1.5, 0) == 0

    def test_interpolate_after_duration(self):
        assert interpolate(0, 50, 20000, 30000, 0) == 50
        assert interpolate(50, 0, 20000, 30000, 0) == 0
        assert interpolate(0, 90, 1.5, 30, 0) == 90

    def test_interpolate_issue_654(self):
        assert [interpolate(0, 90, 1.5, t, 0) for t in (-1, 0, 0.75, 1.5, 5, 30)] == [
            0,
            0,
            45,
            90,
            90,
            90,
        ]

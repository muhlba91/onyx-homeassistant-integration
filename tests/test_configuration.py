"""Test for the ONYX Configuration."""

import pytest

from custom_components.hella_onyx.configuration import (
    Configuration,
    normalize_local_address,
)


class TestConfiguration:
    @pytest.mark.asyncio
    async def test_str(self):
        config = Configuration(1, 2, 3, 4, 5, 6, 7, "finger", "token", None)
        assert (
            str(config)
            == "Configuration(scan_interval=1, min_dim_duration=2, max_dim_duration=3, additional_delay=4, interpolation_frequency=5, closed_tolerance=6, moving_timeout=7, fingerprint=finger, local_address=None)"
        )

    @pytest.mark.asyncio
    async def test_str_local_address(self):
        config = Configuration(1, 2, 3, 4, 5, 6, 7, "finger", "token", "192.168.1.1")
        assert (
            str(config)
            == "Configuration(scan_interval=1, min_dim_duration=2, max_dim_duration=3, additional_delay=4, interpolation_frequency=5, closed_tolerance=6, moving_timeout=7, fingerprint=finger, local_address=192.168.1.1)"
        )

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, None),
            ("", None),
            ("  ", None),
            (5, None),
            ("10.0.0.1", "10.0.0.1"),
            (" 10.0.0.1 ", "10.0.0.1"),
        ],
    )
    def test_normalize_local_address(self, value, expected):
        assert normalize_local_address(value) == expected

    def test_is_local(self):
        assert not Configuration(1, 2, 3, 4, 5, 6, 7, "f", "t", None).is_local
        assert Configuration(1, 2, 3, 4, 5, 6, 7, "f", "t", "10.0.0.1").is_local

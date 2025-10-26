"""Test for the ONYX Configuration."""

import pytest

from custom_components.hella_onyx.configuration import Configuration


class TestConfiguration:
    @pytest.mark.asyncio
    async def test_str(self):
        config = Configuration(1, 2, 3, 4, 5, False, "finger", "token", None)
        assert (
            str(config)
            == "Configuration(scan_interval=1, min_dim_duration=2, max_dim_duration=3, additional_delay=4, interpolation_frequency=5, force_update=False, fingerprint=finger, local_address=None)"
        )

    @pytest.mark.asyncio
    async def test_str_local_address(self):
        config = Configuration(1, 2, 3, 4, 5, False, "finger", "token", "192.168.1.1")
        assert (
            str(config)
            == "Configuration(scan_interval=1, min_dim_duration=2, max_dim_duration=3, additional_delay=4, interpolation_frequency=5, force_update=False, fingerprint=finger, local_address=192.168.1.1)"
        )

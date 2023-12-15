"""Test for the ONYX Configuration."""
import pytest

from custom_components.hella_onyx.configuration import Configuration


class TestConfiguration:
    @pytest.mark.asyncio
    async def test_str(self):
        config = Configuration(1, 2, 3, False, "finger", "token")
        assert (
            str(config)
            == "Configuration(scan_interval=1, min_dim_duration=2, max_dim_duration=3, force_update=False, fingerprint=finger)"
        )

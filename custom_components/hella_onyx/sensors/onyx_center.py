"""The ONYX.CENTER device."""

from homeassistant.helpers.device_registry import DeviceInfo

from ..api_connector import APIConnector
from ..const import DOMAIN


def center_device_info(api: APIConnector, sw_version: str | None = None) -> DeviceInfo:
    """Return the device information of the ONYX.CENTER itself."""
    return DeviceInfo(
        identifiers={(DOMAIN, api.config.fingerprint)},
        name="ONYX.CENTER",
        manufacturer="Hella",
        model="ONYX.CENTER",
        sw_version=sw_version,
    )

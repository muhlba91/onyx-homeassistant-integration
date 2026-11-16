"""The ONYX.CENTER device."""

from homeassistant.helpers.device_registry import DeviceInfo

from ..api_connector import APIConnector
from ..const import DOMAIN


def center_device_info(api: APIConnector, sw_version: str | None = None) -> DeviceInfo:
    """Return the device information of the ONYX.CENTER itself.

    An unknown version is left out, as None would clear the version which
    another entity of the device registered.
    """
    info = DeviceInfo(
        identifiers={(DOMAIN, api.config.fingerprint)},
        name="ONYX.CENTER",
        manufacturer="Hella",
        model="ONYX.CENTER",
    )
    if sw_version is not None:
        info["sw_version"] = sw_version
    return info

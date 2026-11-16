"""The ONYX device types supported by the integration."""

from onyx_client.enum.device_type import DeviceType


def is_supported(device_type: DeviceType) -> bool:
    """Check if the integration creates entities for the device type.

    This is the superset used by the device type sensor and the identify
    button; the other platforms filter for their own device types."""
    return (
        device_type.is_shutter()
        or device_type.is_light()
        or device_type == DeviceType.WEATHER
        or device_type.is_tag()
        or device_type.is_input()
    )

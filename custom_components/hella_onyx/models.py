"""Models for the ONYX integration."""

from dataclasses import dataclass

from .api_connector import APIConnector
from .configuration import Configuration


@dataclass
class OnyxData:
    """Runtime data for the ONYX integration."""

    api: APIConnector
    config: Configuration
    timezone: str

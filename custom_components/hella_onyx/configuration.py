"""Configuration of the ONYX integration."""


def normalize_local_address(value: object) -> str | None:
    """Return the local address stripped, or None if it is empty or not set.

    An empty address must not select the local API: the client would build a
    cloud URL while disabling the TLS verification.
    """
    if not isinstance(value, str):
        return None
    return value.strip() or None


class Configuration:
    """Configuration for the ONYX integration."""

    def __init__(
        self,
        scan_interval,
        min_dim_duration,
        max_dim_duration,
        additional_delay,
        interpolation_frequency,
        closed_tolerance,
        moving_timeout,
        fingerprint,
        token,
        local_address,
    ):
        """Initialize the configuration."""
        self.scan_interval = scan_interval
        self.min_dim_duration = min_dim_duration
        self.max_dim_duration = max_dim_duration
        self.additional_delay = additional_delay
        self.interpolation_frequency = interpolation_frequency
        self.closed_tolerance = closed_tolerance
        self.moving_timeout = moving_timeout
        self.fingerprint = fingerprint
        self.token = token
        self.local_address = local_address

    @property
    def is_local(self) -> bool:
        """Return True if the local API is used, False for the cloud API."""
        return self.local_address is not None

    def __str__(self) -> str:
        return f"Configuration(scan_interval={self.scan_interval}, min_dim_duration={self.min_dim_duration}, max_dim_duration={self.max_dim_duration}, additional_delay={self.additional_delay}, interpolation_frequency={self.interpolation_frequency}, closed_tolerance={self.closed_tolerance}, moving_timeout={self.moving_timeout}, fingerprint={self.fingerprint}, local_address={self.local_address})"

    __repr__ = __str__

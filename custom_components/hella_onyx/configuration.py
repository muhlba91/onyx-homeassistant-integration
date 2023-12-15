"""API connector for the ONYX integration."""


class Configuration:
    """Configuration for the ONYX integration."""

    def __init__(
        self,
        scan_interval,
        min_dim_duration,
        max_dim_duration,
        force_update,
        fingerprint,
        token,
    ):
        """Initialize the configuration."""
        self.scan_interval = scan_interval
        self.min_dim_duration = min_dim_duration
        self.max_dim_duration = max_dim_duration
        self.force_update = force_update
        self.fingerprint = fingerprint
        self.token = token

    def __str__(self) -> str:
        return f"Configuration(scan_interval={self.scan_interval}, min_dim_duration={self.min_dim_duration}, max_dim_duration={self.max_dim_duration}, force_update={self.force_update}, fingerprint={self.fingerprint})"

"""Custom Data Monitoring exception types."""


class DimException(Exception):
    """Generic Exception thrown"""

    def __init__(self, message):
        """Initialize exception."""
        super().__init__(message)


class NoStartDateException(DimException):
    """Exception thrown when no start date has been defined."""

    def __init__(self, slug, message="Project has no start date."):
        """Initialize exception."""
        super().__init__(f"{slug} -> {message}")


class StartEndException(DimException):
    """Exception thrown when no start date has been defined."""

    def __init__(
        self, slug, message="Start date should be less than End date."
    ):
        """Initialize exception."""
        super().__init__(f"{slug} -> {message}")

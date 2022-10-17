
"""Custom Data Monitoring exception types."""

class OpmonException(Exception):
    """Generic Exception thrown """

    def __init__(self, message):
        """Initialize exception."""
        super().__init__(message)

class NoStartDateException(OpmonException):
    """Exception thrown when no start date has been defined."""

    def __init__(self, slug, message="Project has no start date."):
        """Initialize exception."""
        super().__init__(f"{slug} -> {message}")

class StartEndException(OpmonException):
    """Exception thrown when no start date has been defined."""

    def __init__(self, slug, message="Start date should be less than End date."):
        """Initialize exception."""
        super().__init__(f"{slug} -> {message}")



class ConfigurationException(OpmonException):
    """Exception thrown when the configuration is incorrect."""

    def __init__(self, slug, message="Project has been incorrectly configured."):
        """Initialize exception."""
        super().__init__(f"{slug} -> {message}")


class StatisticNotImplementedForTypeException(OpmonException):
    """Exception thrown when statistic is not implemented for metric type."""

    def __init__(self, slug, message="Statistic not implemented for metric type."):
        """Initialize exception."""
        super().__init__(f"{slug} -> {message}")
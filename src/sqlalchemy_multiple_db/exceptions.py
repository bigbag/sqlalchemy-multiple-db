class ConfigurationError(ValueError):
    """Raised when database-manager configuration is invalid."""


class ManagerClosedError(RuntimeError):
    """Raised when an operation is requested after manager disposal."""

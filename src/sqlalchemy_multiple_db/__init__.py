"""Explicit SQLAlchemy management for multiple named databases."""

from .config import DatabaseConfig
from .exceptions import ConfigurationError, ManagerClosedError
from .manager import DatabaseManager

__version__ = "3.1.0"
__all__ = [
    "ConfigurationError",
    "DatabaseConfig",
    "DatabaseManager",
    "ManagerClosedError",
    "__version__",
]

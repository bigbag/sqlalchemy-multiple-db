from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """Connection and session options for one named SQLAlchemy database."""

    url: str
    engine_options: Mapping[str, Any] = field(default_factory=dict)
    session_options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.url, str) or not self.url.strip():
            raise ConfigurationError("url must be a non-empty string")
        if not isinstance(self.engine_options, Mapping):
            raise ConfigurationError("engine_options must be a mapping")
        if not isinstance(self.session_options, Mapping):
            raise ConfigurationError("session_options must be a mapping")

        object.__setattr__(self, "engine_options", MappingProxyType(dict(self.engine_options)))
        object.__setattr__(self, "session_options", MappingProxyType(dict(self.session_options)))

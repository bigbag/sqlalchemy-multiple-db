from __future__ import annotations

import logging
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from types import TracebackType

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .config import DatabaseConfig
from .exceptions import ConfigurationError, ManagerClosedError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Own synchronous SQLAlchemy engines for explicitly named databases."""

    def __init__(self, configurations: Mapping[str, DatabaseConfig]) -> None:
        if not isinstance(configurations, Mapping) or not configurations:
            raise ConfigurationError("configurations must contain at least one database")

        validated: dict[str, DatabaseConfig] = {}
        for name, config in configurations.items():
            if not isinstance(name, str) or not name.strip():
                raise ConfigurationError("database names must be non-empty strings")
            if not isinstance(config, DatabaseConfig):
                raise ConfigurationError(f"configuration for {name!r} must be a DatabaseConfig")
            validated[name] = config

        self._engines: dict[str, Engine] = {}
        self._session_factories: dict[str, sessionmaker[Session]] = {}
        self._closed = False
        try:
            for name, config in validated.items():
                engine = create_engine(config.url, **dict(config.engine_options))
                self._engines[name] = engine
                self._session_factories[name] = sessionmaker(
                    bind=engine,
                    **dict(config.session_options),
                )
        except (ArgumentError, TypeError) as error:
            for engine in self._engines.values():
                engine.dispose()
            raise ConfigurationError(f"invalid configuration: {error}") from error

    def __enter__(self) -> DatabaseManager:
        self._ensure_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    @contextmanager
    def session(self, name: str) -> Generator[Session, None, None]:
        """Yield a transactional session for `name`."""
        factory = self._get_session_factory(name)
        session = factory()
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    def healthcheck(self) -> dict[str, bool]:
        """Return whether each configured engine can execute `SELECT 1`."""
        self._ensure_open()
        status: dict[str, bool] = {}
        for name, engine in self._engines.items():
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
            except SQLAlchemyError:
                logger.warning("Database health check failed for %s", name, exc_info=True)
                status[name] = False
            else:
                status[name] = True
        return status

    def close(self) -> None:
        """Dispose all engines. Repeated calls are safe."""
        if self._closed:
            return
        for engine in self._engines.values():
            engine.dispose()
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise ManagerClosedError("DatabaseManager has been closed")

    def _get_session_factory(self, name: str) -> sessionmaker[Session]:
        self._ensure_open()
        try:
            return self._session_factories[name]
        except KeyError as error:
            available = ", ".join(sorted(self._session_factories))
            raise KeyError(
                f"unknown database {name!r}; available databases: {available}"
            ) from error

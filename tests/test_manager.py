from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy_multiple_db import (
    ConfigurationError,
    DatabaseConfig,
    DatabaseManager,
    ManagerClosedError,
)


@pytest.fixture
def manager() -> Generator[DatabaseManager, None, None]:
    databases = DatabaseManager(
        {
            "primary": DatabaseConfig(url="sqlite:///:memory:"),
            "analytics": DatabaseConfig(url="sqlite:///:memory:"),
        }
    )
    yield databases
    databases.close()


def test_session_commits_to_the_selected_database(manager: DatabaseManager) -> None:
    with manager.session("primary") as session:
        session.execute(text("CREATE TABLE records (value INTEGER NOT NULL)"))
        session.execute(text("INSERT INTO records (value) VALUES (1)"))

    with manager.session("primary") as session:
        assert session.scalar(text("SELECT COUNT(*) FROM records")) == 1


def test_session_rolls_back_when_the_block_raises(manager: DatabaseManager) -> None:
    with manager.session("primary") as session:
        session.execute(text("CREATE TABLE records (value INTEGER NOT NULL)"))

    with (
        pytest.raises(RuntimeError, match="abort transaction"),
        manager.session("primary") as session,
    ):
        session.execute(text("INSERT INTO records (value) VALUES (1)"))
        raise RuntimeError("abort transaction")

    with manager.session("primary") as session:
        assert session.scalar(text("SELECT COUNT(*) FROM records")) == 0


def test_session_context_uses_fresh_sessions_and_closes_them(manager: DatabaseManager) -> None:
    first_session = MagicMock()
    second_session = MagicMock()
    factory = MagicMock(side_effect=[first_session, second_session])
    manager._session_factories["primary"] = factory

    with manager.session("primary") as first:
        assert first is first_session
    with manager.session("primary") as second:
        assert second is second_session

    assert first_session is not second_session
    first_session.commit.assert_called_once_with()
    second_session.commit.assert_called_once_with()
    first_session.close.assert_called_once_with()
    second_session.close.assert_called_once_with()


def test_named_databases_are_independent(manager: DatabaseManager) -> None:
    with manager.session("primary") as session:
        session.execute(text("CREATE TABLE records (value INTEGER NOT NULL)"))

    with manager.session("analytics") as session:
        assert (
            session.scalar(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'records'")
            )
            == 0
        )


def test_unknown_database_name_lists_the_available_names(manager: DatabaseManager) -> None:
    with (
        pytest.raises(KeyError, match="unknown database 'missing'.*analytics.*primary"),
        manager.session("missing"),
    ):
        pass


def test_manager_requires_a_non_empty_mapping() -> None:
    with pytest.raises(ConfigurationError, match="at least one database"):
        DatabaseManager({})


def test_manager_rejects_invalid_names_and_configs() -> None:
    with pytest.raises(ConfigurationError, match="database names must be non-empty strings"):
        DatabaseManager({"": DatabaseConfig(url="sqlite://")})
    with pytest.raises(ConfigurationError, match="must be a DatabaseConfig"):
        DatabaseManager({"primary": "sqlite://"})  # type: ignore[dict-item]


def test_close_is_idempotent_and_blocks_future_operations() -> None:
    databases = DatabaseManager({"primary": DatabaseConfig(url="sqlite://")})
    databases.close()
    databases.close()

    with pytest.raises(ManagerClosedError, match="has been closed"):
        databases.healthcheck()


def test_context_manager_closes_the_manager() -> None:
    with DatabaseManager({"primary": DatabaseConfig(url="sqlite://")}) as databases:
        assert databases.healthcheck() == {"primary": True}

    with pytest.raises(ManagerClosedError, match="has been closed"), databases.session("primary"):
        pass


def test_healthcheck_continues_after_a_sqlalchemy_failure(
    manager: DatabaseManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FailingConnection:
        def __enter__(self) -> FailingConnection:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def execute(self, _: object) -> None:
            raise SQLAlchemyError("offline")

    class FailingEngine:
        def connect(self) -> FailingConnection:
            return FailingConnection()

        def dispose(self) -> None:
            return None

    monkeypatch.setitem(manager._engines, "analytics", FailingEngine())  # type: ignore[arg-type]

    assert manager.healthcheck() == {"primary": True, "analytics": False}

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy_multiple_db import DEFAULT_DB_NAME, DBConfig, DBHelper, db


def test_get_session_without_setup():
    with pytest.raises(AttributeError):
        db.sessions


@pytest.fixture
def db_helper():
    helper = DBHelper()
    config = {DEFAULT_DB_NAME: DBConfig(dsn="sqlite:///:memory:")}
    helper.setup(config)
    return helper


def test_session_scope_successful_transaction(db_helper):
    mock_session = MagicMock()
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance
    db_helper.sessions = {DEFAULT_DB_NAME: mock_session}

    with db_helper.session_scope() as session:
        assert session == mock_session_instance

    mock_session.assert_called_once()
    mock_session.remove.assert_called_once()


def test_session_scope_with_exception(db_helper):
    mock_session = MagicMock()
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance
    db_helper.sessions = {DEFAULT_DB_NAME: mock_session}

    with pytest.raises(ValueError):
        with db_helper.session_scope():
            raise ValueError("Test exception")

    mock_session.assert_called_once()
    mock_session.remove.assert_called_once()


def test_session_scope_with_non_default_db(db_helper):
    custom_db = "custom_db"
    mock_session = MagicMock()
    mock_session_instance = MagicMock()
    mock_session.return_value = mock_session_instance
    db_helper.sessions = {custom_db: mock_session}

    with db_helper.session_scope(db_name=custom_db) as session:
        assert session == mock_session_instance

    mock_session.assert_called_once()
    mock_session.remove.assert_called_once()


def test_session_scope_with_invalid_db_name(db_helper):
    invalid_db = "invalid_db"

    with pytest.raises(ValueError, match=f"No session found for database: {invalid_db}"):
        with db_helper.session_scope(db_name=invalid_db):
            pass


class TestGetStatusInfo:
    def test_error(self):
        class MockSession:
            def execute(self, *args, **kwargs):
                raise SQLAlchemyError()

            def close(self, *args, **kwargs):
                pass

            def remove(self, *args, **kwargs):
                pass

        db.sessions = {"default": MockSession()}

        full_status_info, full_status = db.get_status_info()
        assert full_status is False
        assert full_status_info == {"default": {"status": "FAILED"}}

    def test_success(self):
        db.setup(DBConfig(dsn="sqlite://"))

        full_status_info, full_status = db.get_status_info()
        assert full_status is True
        assert full_status_info == {"default": {"status": "OK"}}

        db.shutdown()

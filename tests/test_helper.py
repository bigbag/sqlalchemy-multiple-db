import pytest
from sqlalchemy.orm import scoped_session

from sqlalchemy_multiple_db import DBConfig, db


def test_get_session_without_setup():
    with pytest.raises(AttributeError):
        db.sessions


def test_with_one_db():
    db.setup(DBConfig(dsn="sqlite://"))

    assert "default" in db.sessions
    assert len(db.sessions) == 1
    assert isinstance(db.sessions["default"], scoped_session)

    with db.session_scope() as session:
        assert session.execute("select 1;")

    db.shutdown()


def test_with__multiple_db():
    db.setup({"test1": DBConfig(dsn="sqlite://"), "test2": DBConfig(dsn="sqlite://")})

    assert "test1" in db.sessions
    assert "test2" in db.sessions
    assert len(db.sessions) == 2
    assert isinstance(db.sessions["test1"], scoped_session)
    assert isinstance(db.sessions["test2"], scoped_session)

    with db.session_scope("test1") as session:
        assert session.execute("select 1;")

    with db.session_scope("test2") as session:
        assert session.execute("select 1;")

    db.shutdown()


class TestGetStatusInfo:
    def test_error(self):
        class MockSession:
            def execute(self, *args, **kwargs):
                raise Exception()

            def close(self, *args, **kwargs):
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

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from json import dumps, loads
from typing import Any, Dict, Generator, Tuple, Union

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)


DEFAULT_DB_NAME = "default"
DEFAULT_SESSION_OPTIONS = {"autocommit": False, "autoflush": False, "expire_on_commit": False}
DEFAULT_ENGINE_OPTIONS = {
    "pool_size": 50,
    "pool_pre_ping": True,
    "echo": False,
    "json_serializer": dumps,
    "json_deserializer": loads,
}


@dataclass
class DBConfig:
    dsn: str
    session_options: Dict[str, Any] = field(default_factory=dict)
    engine_options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.session_options = {**DEFAULT_SESSION_OPTIONS, **self.session_options}
        self.engine_options = {**DEFAULT_ENGINE_OPTIONS, **self.engine_options}


@dataclass
class DBHelper:
    sessions: Dict[str, scoped_session] = field(init=False, repr=False)
    config: Dict[str, DBConfig] = field(init=False, repr=False)

    def __getattribute__(self, db_name):
        try:
            return object.__getattribute__(self, db_name)
        except AttributeError as exc:
            if db_name in ["sessions", "config"]:
                print(f"DB: You need to call setup() for getting attribute {db_name}")
            raise exc

    def create_scoped_session(self, config: DBConfig) -> scoped_session:
        engine_options = config.engine_options or {}
        session_options = config.session_options or {}

        session = scoped_session(
            sessionmaker(bind=create_engine(config.dsn, **engine_options), **session_options)
        )
        return session  # type: ignore

    def setup(self, config: Union[DBConfig, Dict[str, DBConfig]]):
        if isinstance(config, DBConfig):
            config = {DEFAULT_DB_NAME: config}

        self.config = config

        self.sessions = {}
        for db_name, cfg in config.items():
            self.sessions[db_name] = self.create_scoped_session(cfg)

    def shutdown(self) -> None:
        for session in self.sessions.values():
            session.remove()
        self.sessions.clear()

    @contextmanager
    def session_scope(self, db_name: str = DEFAULT_DB_NAME) -> Generator[Session, None, None]:
        session = self.sessions.get(db_name)
        if not session:
            raise ValueError(f"No session found for database: {db_name}")
        try:
            yield session()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.remove()

    def get_status_info(self) -> Tuple[Dict[str, Dict[str, str]], bool]:
        full_status = True
        full_status_info = {}
        for db_name, session in self.sessions.items():
            status = True
            try:
                session.execute(text("SELECT 1"))
            except SQLAlchemyError as e:
                logger.exception(f"Database {db_name} connection failed: {e}")
                status &= False
                full_status &= False
            finally:
                session.remove()

            full_status_info[db_name] = {"status": "OK"} if status else {"status": "FAILED"}

        return full_status_info, full_status


db = DBHelper()

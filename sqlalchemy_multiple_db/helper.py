import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from json import dumps, loads
from typing import Any, Dict, Optional, Tuple, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

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
    session_options: Optional[Dict[str, Any]] = None
    engine_options: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        session_options = DEFAULT_SESSION_OPTIONS
        session_options.update(self.session_options or {})
        self.session_options = session_options

        engine_options = DEFAULT_ENGINE_OPTIONS
        engine_options.update(self.engine_options or {})
        self.engine_options = engine_options


@dataclass
class DBHelper:
    sessions: Dict[str, Session] = field(init=False, repr=False)
    config: Dict[str, DBConfig] = field(init=False, repr=False)

    def __getattribute__(self, db_name):
        try:
            return object.__getattribute__(self, db_name)
        except AttributeError as exc:
            if db_name in ["sessions", "config"]:
                print(f"DB: You need to call setup() for getting attribute {db_name}")
            raise exc

    def create_scoped_session(self, config: DBConfig) -> Session:
        session: scoped_session = scoped_session(
            sessionmaker(
                bind=create_engine(config.dsn, **config.engine_options), **config.session_options
            )
        )
        return session

    def setup(self, config: Union[DBConfig, Dict[str, DBConfig]]):
        if isinstance(config, DBConfig):
            config = {DEFAULT_DB_NAME: config}

        self.config = config

        self.sessions = {}
        for db_name, cfg in config.items():
            self.sessions[db_name] = self.create_scoped_session(cfg)

    def shutdown(self):
        for session in self.sessions.values():
            session.remove()

    @contextmanager
    def session_scope(self, db_name: str = DEFAULT_DB_NAME):
        session = db.sessions[db_name]
        try:
            yield session
        finally:
            session.close()

    def get_status_info(self) -> Tuple[Dict[str, Any], bool]:
        full_status = True
        full_status_info = {}

        for db_name, session in self.sessions.items():
            status = True
            try:
                session.execute("select 1;")
            except Exception as e:
                status &= False
                full_status &= False
                logger.exception(e)
            finally:
                session.close()

            full_status_info[db_name] = {"status": "OK"} if status else {"status": "FAILED"}

        return full_status_info, full_status


db = DBHelper()

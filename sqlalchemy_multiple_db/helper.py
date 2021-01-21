import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from json import dumps, loads
from typing import Any, Callable, Dict, Tuple, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    dsn: str
    pool_size: int = 50
    pool_pre_ping: bool = True
    echo: bool = False
    auto_commit: bool = False
    auto_flush: bool = False
    expire_on_commit: bool = False
    executemany_mode: str = ""
    json_serializer: Callable = dumps
    json_deserializer: Callable = loads


DEFAULT_DB_NAME = "default"


@dataclass
class DBHelper:
    sessions: Dict[str, Session] = field(init=False, repr=False)
    config: Dict[str, DBConfig] = field(init=False, repr=False)

    def __getattribute__(self, db_name):
        try:
            return object.__getattribute__(self, db_name)
        except AttributeError as exc:
            if db_name == "sessions":
                print(f"DB: You need to call setup() for getting attribute {db_name}")
            raise exc

    def create_scoped_session(self, config: DBConfig) -> Session:
        engine = create_engine(
            config.dsn,
            pool_size=config.pool_size,
            pool_pre_ping=config.pool_pre_ping,
            echo=config.echo,
            json_serializer=config.json_serializer,
            json_deserializer=config.json_deserializer,
            executemany_mode=config.executemany_mode or None,
        )
        session: Session = scoped_session(
            sessionmaker(
                autocommit=config.auto_commit,
                autoflush=config.auto_flush,
                expire_on_commit=config.expire_on_commit,
                bind=engine,
            )
        )
        return session

    def setup(self, config: Union[DBConfig, Dict[str, DBConfig]]):
        if isinstance(config, DBConfig):
            config = {self.DEFAULT_DB_NAME: config}

        self.config = config

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
                session.execute("select version();")
            except Exception as e:
                status &= False
                full_status &= False
                logger.exception(e)
            finally:
                session.close()

            full_status_info[db_name] = {"status": "OK"} if status else {"status": "FAILED"}, status

        return full_status_info, full_status


db = DBHelper()


def get_session(db_name: str = DEFAULT_DB_NAME):
    session = db.sessions[db_name]
    try:
        yield session
    finally:
        session.close()

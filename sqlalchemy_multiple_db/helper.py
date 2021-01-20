import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from json import dumps, loads
from typing import Any, Dict, Tuple

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import declarative_base
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

    def get_dsn_as_dict(self) -> Dict[str, Any]:
        conf_url = make_url(self.dsn)
        return {
            "username": conf_url.username,
            "database": conf_url.database,
            "port": conf_url.port,
            "host": conf_url.host,
            "password": conf_url.password,
        }


@dataclass
class DB:
    config: DBConfig = field(init=False, repr=False)
    session: Session = field(init=False, repr=False)

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError as exc:
            if name in ["config", "session"]:
                print(f"DB: You need to call setup() for getting attribute {name}")
            raise exc

    def setup(self, config: DBConfig):
        logger.info("Init connection pool")

        self.config = config
        engine = create_engine(
            config.dsn,
            pool_size=config.pool_size,
            pool_pre_ping=config.pool_pre_ping,
            echo=config.echo,
            json_serializer=dumps,
            json_deserializer=loads,
            executemany_mode=config.executemany_mode or None,
        )
        self.session = scoped_session(
            sessionmaker(
                autocommit=config.auto_commit,
                autoflush=config.auto_flush,
                expire_on_commit=config.expire_on_commit,
                bind=engine,
            )
        )

    def shutdown(self):
        logger.info("Shutdown connection pool")
        self.session.remove()

    @contextmanager
    def session_scope(self):
        yield self.session
        self.session.close()

    def get_status_info(self) -> Tuple[Dict[str, Any], bool]:
        status = True
        session = self.session()
        try:
            session.execute("select version();")
        except Exception as e:
            status &= False
            logger.exception(e)
        finally:
            session.close()

        return {"status": "OK"} if status else {"status": "FAILED"}, status


db = DB()


BaseModel = declarative_base()


def get_session():
    session = db.session
    try:
        yield session
    finally:
        session.close()

"""Check named databases and pass engine and session configuration options."""

from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import text

from sqlalchemy_multiple_db import DatabaseConfig, DatabaseManager


def main() -> None:
    with TemporaryDirectory(prefix="sqlalchemy-multiple-db-") as directory:
        database_directory = Path(directory)
        configurations = {
            "primary": DatabaseConfig(
                url=f"sqlite:///{database_directory / 'primary.db'}",
                engine_options={"pool_pre_ping": True},
                session_options={"expire_on_commit": False},
            ),
            "analytics": DatabaseConfig(
                url=f"sqlite:///{database_directory / 'analytics.db'}",
                engine_options={"pool_pre_ping": True},
                session_options={"expire_on_commit": False},
            ),
        }

        with DatabaseManager(configurations) as databases:
            health = databases.healthcheck()
            assert health == {"primary": True, "analytics": True}

            for name in health:
                with databases.session(name) as session:
                    assert session.scalar(text("SELECT 1")) == 1

        print(f"Health check: {health}")


if __name__ == "__main__":
    main()

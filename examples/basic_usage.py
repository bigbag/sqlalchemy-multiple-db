"""Create and query two isolated named SQLite databases."""

from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import text

from sqlalchemy_multiple_db import DatabaseConfig, DatabaseManager


def main() -> None:
    with TemporaryDirectory(prefix="sqlalchemy-multiple-db-") as directory:
        database_directory = Path(directory)
        configurations = {
            "primary": DatabaseConfig(url=f"sqlite:///{database_directory / 'primary.db'}"),
            "analytics": DatabaseConfig(url=f"sqlite:///{database_directory / 'analytics.db'}"),
        }

        with DatabaseManager(configurations) as databases:
            with databases.session("primary") as session:
                session.execute(text("CREATE TABLE events (name TEXT NOT NULL)"))
                session.execute(text("INSERT INTO events (name) VALUES ('deployment')"))

            with databases.session("analytics") as session:
                session.execute(text("CREATE TABLE reports (name TEXT NOT NULL)"))
                session.execute(text("INSERT INTO reports (name) VALUES ('daily summary')"))

            with databases.session("primary") as session:
                primary_event = session.scalar(text("SELECT name FROM events"))
            with databases.session("analytics") as session:
                analytics_report = session.scalar(text("SELECT name FROM reports"))

        print(f"Primary event: {primary_event}")
        print(f"Analytics report: {analytics_report}")


if __name__ == "__main__":
    main()

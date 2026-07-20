"""Show that a failed session block rolls back its transaction."""

from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import text

from sqlalchemy_multiple_db import DatabaseConfig, DatabaseManager


def main() -> None:
    with TemporaryDirectory(prefix="sqlalchemy-multiple-db-") as directory:
        database_path = Path(directory) / "primary.db"
        configurations = {"primary": DatabaseConfig(url=f"sqlite:///{database_path}")}

        with DatabaseManager(configurations) as databases:
            with databases.session("primary") as session:
                session.execute(text("CREATE TABLE entries (name TEXT NOT NULL)"))

            try:
                with databases.session("primary") as session:
                    session.execute(text("INSERT INTO entries (name) VALUES ('not persisted')"))
                    raise RuntimeError("simulate a failed unit of work")
            except RuntimeError:
                pass

            with databases.session("primary") as session:
                entry_count = session.scalar(text("SELECT COUNT(*) FROM entries"))

        assert entry_count == 0
        print(f"Rollback confirmed: {entry_count} entries")


if __name__ == "__main__":
    main()

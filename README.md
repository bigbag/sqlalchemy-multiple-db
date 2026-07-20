# sqlalchemy-multiple-db

Explicit, typed SQLAlchemy 2.x session management for multiple named databases.

## Requirements

- Python 3.11, 3.12, 3.13, or 3.14
- SQLAlchemy 2.x (installed automatically)

## Installation

```bash
uv add sqlalchemy-multiple-db
# or
uv pip install sqlalchemy-multiple-db
```

## Quick start

```python
from sqlalchemy import text
from sqlalchemy_multiple_db import DatabaseConfig, DatabaseManager

configs = {
    "primary": DatabaseConfig(url="sqlite:///primary.db"),
    "analytics": DatabaseConfig(url="sqlite:///analytics.db"),
}

with DatabaseManager(configs) as databases:
    with databases.session("primary") as session:
        session.execute(text("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY)"))
        session.execute(text("INSERT INTO events DEFAULT VALUES"))

    with databases.session("analytics") as session:
        session.execute(text("SELECT 1"))

    assert databases.healthcheck() == {"primary": True, "analytics": True}
```

Each `session(name)` call creates a new SQLAlchemy `Session`. A normal block commits; an exception
rolls back and is re-raised; the session always closes. Call `close()` when not using the manager as a
context manager. `close()` is idempotent, but the manager cannot be used afterward.

## Configuration

`DatabaseConfig(url, engine_options={}, session_options={})` forwards option mappings to SQLAlchemy's
`create_engine` and `sessionmaker`. Options are copied at construction. The library deliberately does
not choose pool sizes or deprecated autocommit behavior; configure dialect-specific options explicitly
when needed.

`healthcheck()` runs `SELECT 1` for every configured engine and returns a `{name: bool}` mapping.
SQLAlchemy connection failures are logged and reported as `False` without stopping checks for other
databases.

## Migrating from 2.x

| 2.x | 3.0 |
| --- | --- |
| `DBConfig(dsn="...")` | `DatabaseConfig(url="...")` |
| `DBHelper` or global `db` | `DatabaseManager(configurations)` |
| `setup()` | construct the manager |
| `session_scope()` | `session(name)` |
| `get_status_info()` | `healthcheck()` |
| `shutdown()` | `close()` or `with DatabaseManager(...)` |

There is no global manager or implicit `default` database in 3.0. Name every database explicitly.

## Examples

Each example uses temporary SQLite files and needs no external database server:

- [basic_usage.py](examples/basic_usage.py) — create, write to, and query isolated primary and analytics databases.
- [transaction_rollback.py](examples/transaction_rollback.py) — verify that an exception rolls back a transaction.
- [healthcheck_and_options.py](examples/healthcheck_and_options.py) — configure engine/session options and inspect database health.

Run an example from a synced checkout:

```bash
uv run python examples/basic_usage.py
```

## Development

```bash
uv sync --all-groups
uv run pytest
uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src
uv build
```

Use `uv add <package>` to add a dependency and `uv lock --upgrade` to refresh all locked dependency
versions. Commit every `pyproject.toml` and `uv.lock` change together.

## License

Apache-2.0. See [LICENSE](LICENSE).

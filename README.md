# sqlalchemy-multiple-db

[![CI](https://github.com/bigbag/sqlalchemy-multiple-db/workflows/CI/badge.svg)](https://github.com/bigbag/sqlalchemy-multiple-db/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/bigbag/sqlalchemy-multiple-db/branch/main/graph/badge.svg)](https://codecov.io/gh/bigbag/sqlalchemy-multiple-db)
[![pypi](https://img.shields.io/pypi/v/sqlalchemy-multiple-db.svg)](https://pypi.python.org/pypi/sqlalchemy-multiple-db)
[![downloads](https://img.shields.io/pypi/dm/sqlalchemy-multiple-db.svg)](https://pypistats.org/packages/sqlalchemy-multiple-db)
[![versions](https://img.shields.io/pypi/pyversions/sqlalchemy-multiple-db.svg)](https://github.com/bigbag/sqlalchemy-multiple-db)
[![license](https://img.shields.io/github/license/bigbag/sqlalchemy-multiple-db.svg)](https://github.com/bigbag/sqlalchemy-multiple-db/blob/master/LICENSE)

**sqlalchemy-multiple-db** helper for easily connect to multiple databases.


## Installation

sqlalchemy-multiple-db is available on PyPI.
Use pip to install:

    $ pip install sqlalchemy-multiple-db

## Basic Usage
```py
from sqlalchemy_multiple_db import DBConfig, db

db.setup({"test1": DBConfig(dsn="sqlite://"), "test2": DBConfig(dsn="sqlite://")})

with db.session_scope("test1") as session:
    assert session.execute("select 1;")

with db.session_scope("test2") as session:
    assert session.execute("select 1;")

db.shutdown()

db.setup(DBConfig(dsn="sqlite://"))

with db.session_scope() as session:
    assert session.execute("select 1;")

db.shutdown()

```

## License

sqlalchemy-multiple-db is developed and distributed under the Apache 2.0 license.

## Reporting a Security Vulnerability

See our [security policy](https://github.com/bigbag/sqlalchemy-multiple-db/security/policy).

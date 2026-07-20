import sqlalchemy_multiple_db


def test_package_exposes_only_v3_public_api() -> None:
    assert sqlalchemy_multiple_db.__all__ == [
        "ConfigurationError",
        "DatabaseConfig",
        "DatabaseManager",
        "ManagerClosedError",
        "__version__",
    ]
    assert sqlalchemy_multiple_db.__version__ == "3.0.0"
    assert not hasattr(sqlalchemy_multiple_db, "DBConfig")
    assert not hasattr(sqlalchemy_multiple_db, "DBHelper")
    assert not hasattr(sqlalchemy_multiple_db, "db")

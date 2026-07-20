from __future__ import annotations

from collections.abc import Mapping

import pytest

from sqlalchemy_multiple_db import ConfigurationError, DatabaseConfig


def test_config_rejects_blank_url() -> None:
    with pytest.raises(ConfigurationError, match="url must be a non-empty string"):
        DatabaseConfig(url="   ")


@pytest.mark.parametrize("url", [None, 123])
def test_config_rejects_non_string_url(url: object) -> None:
    with pytest.raises(ConfigurationError, match="url must be a non-empty string"):
        DatabaseConfig(url=url)  # type: ignore[arg-type]


def test_config_copies_option_mappings() -> None:
    engine_options = {"pool_pre_ping": True}
    session_options = {"expire_on_commit": False}

    config = DatabaseConfig(
        url="sqlite://",
        engine_options=engine_options,
        session_options=session_options,
    )
    engine_options["echo"] = True
    session_options["autoflush"] = False

    assert config.engine_options == {"pool_pre_ping": True}
    assert config.session_options == {"expire_on_commit": False}
    assert isinstance(config.engine_options, Mapping)
    with pytest.raises(TypeError):
        config.engine_options["echo"] = True  # type: ignore[index]


def test_config_rejects_non_mapping_options() -> None:
    with pytest.raises(ConfigurationError, match="engine_options must be a mapping"):
        DatabaseConfig(url="sqlite://", engine_options=[("echo", True)])  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError, match="session_options must be a mapping"):
        DatabaseConfig(url="sqlite://", session_options=[("autoflush", False)])  # type: ignore[arg-type]

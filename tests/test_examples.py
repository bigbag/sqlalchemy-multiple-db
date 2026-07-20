from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).parent.parent / "examples"


@pytest.mark.parametrize(
    ("example_name", "expected_output"),
    [
        ("basic_usage.py", "Primary event: deployment"),
        ("transaction_rollback.py", "Rollback confirmed: 0 entries"),
        ("healthcheck_and_options.py", "Health check: {'primary': True, 'analytics': True}"),
    ],
)
def test_example_runs_successfully(example_name: str, expected_output: str) -> None:
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / example_name)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert expected_output in result.stdout

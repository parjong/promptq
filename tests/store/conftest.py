import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from promptq.store.base import Store
from promptq.store.directory import DirectoryStore


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "home"


@pytest.fixture
def store(home: Path) -> Store:
    """Subject of the contract tests every Store implementation must pass (D16).

    Parametrize here when a second implementation appears.
    """
    return DirectoryStore(home, create=True)


def age(path: Path, delta: timedelta) -> None:
    """Move the file's mtime `delta` into the past."""
    ts = (datetime.now(UTC) - delta).timestamp()
    os.utime(path, (ts, ts))

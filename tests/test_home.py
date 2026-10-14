from pathlib import Path

import pytest

from promptq.errors import InvalidHome
from promptq.home import resolve_home
from promptq.models import HomeSource


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROMPTQ_HOME", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)


def test_argument_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROMPTQ_HOME", "/env")
    result = resolve_home("/arg")
    assert (result.path, result.source) == (Path("/arg"), HomeSource.ARGUMENT)


def test_env_over_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROMPTQ_HOME", "/env")
    monkeypatch.setenv("XDG_STATE_HOME", "/xdg")
    result = resolve_home()
    assert (result.path, result.source) == (Path("/env"), HomeSource.PROMPTQ_HOME)


def test_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", "/xdg")
    result = resolve_home()
    assert (result.path, result.source) == (Path("/xdg/promptq"), HomeSource.XDG_STATE_HOME)


def test_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    result = resolve_home()
    assert result.path == tmp_path / ".local" / "state" / "promptq"
    assert result.source is HomeSource.DEFAULT


def test_empty_env_is_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROMPTQ_HOME", "")
    monkeypatch.setenv("XDG_STATE_HOME", "")
    assert resolve_home().source is HomeSource.DEFAULT


def test_relative_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(InvalidHome):
        resolve_home("rel/path")
    monkeypatch.setenv("PROMPTQ_HOME", "rel")
    with pytest.raises(InvalidHome):
        resolve_home()

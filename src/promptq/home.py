"""Store path resolution (08). Never touches the filesystem."""

from __future__ import annotations

import os
from pathlib import Path

from promptq.errors import InvalidHome
from promptq.models import HomeResolution, HomeSource

StrPath = str | os.PathLike[str]


def _absolute(value: str, *, source: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise InvalidHome(f"{source} must be an absolute path: {value!r}")
    return path


def resolve_home(home: StrPath | None = None) -> HomeResolution:
    """Resolve: argument > $PROMPTQ_HOME > $XDG_STATE_HOME/promptq > ~/.local/state/promptq.

    An empty environment variable counts as unset. Relative paths raise InvalidHome.
    """
    if home is not None:
        return HomeResolution(
            _absolute(os.fspath(home), source="the home argument"), HomeSource.ARGUMENT
        )
    if env := os.environ.get("PROMPTQ_HOME"):
        return HomeResolution(_absolute(env, source="PROMPTQ_HOME"), HomeSource.PROMPTQ_HOME)
    if xdg := os.environ.get("XDG_STATE_HOME"):
        path = _absolute(xdg, source="XDG_STATE_HOME") / "promptq"
        return HomeResolution(path, HomeSource.XDG_STATE_HOME)
    return HomeResolution(Path.home() / ".local" / "state" / "promptq", HomeSource.DEFAULT)

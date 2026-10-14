"""저장소 경로 해석 (08). 파일시스템에 접근하지 않는다."""

from __future__ import annotations

import os
from pathlib import Path

from promptq.errors import InvalidHome
from promptq.models import HomeResolution, HomeSource

StrPath = str | os.PathLike[str]


def _absolute(value: str, *, source: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise InvalidHome(f"{source}는 절대 경로여야 합니다: {value!r}")
    return path


def resolve_home(home: StrPath | None = None) -> HomeResolution:
    """인자 > $PROMPTQ_HOME > $XDG_STATE_HOME/promptq > ~/.local/state/promptq 순으로 해석한다.

    빈 환경 변수는 미설정으로 본다. 상대 경로는 InvalidHome이다.
    """
    if home is not None:
        return HomeResolution(_absolute(os.fspath(home), source="home 인자"), HomeSource.ARGUMENT)
    if env := os.environ.get("PROMPTQ_HOME"):
        return HomeResolution(_absolute(env, source="PROMPTQ_HOME"), HomeSource.PROMPTQ_HOME)
    if xdg := os.environ.get("XDG_STATE_HOME"):
        path = _absolute(xdg, source="XDG_STATE_HOME") / "promptq"
        return HomeResolution(path, HomeSource.XDG_STATE_HOME)
    return HomeResolution(Path.home() / ".local" / "state" / "promptq", HomeSource.DEFAULT)

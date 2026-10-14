"""값 객체. promptq의 다른 모듈을 런타임에 import하지 않는다."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from promptq.naming import Name


class State(enum.StrEnum):
    PENDING = "pending"
    CLAIMED = "claimed"


@dataclass(frozen=True, slots=True)
class Enqueued:
    name: Name
    enqueued: Literal[True] = True


@dataclass(frozen=True, slots=True)
class Ignored:
    """같은 이름이 이미 있어서 무시됨."""

    name: Name
    existing_state: State
    enqueued: Literal[False] = False


EnqueueResult = Enqueued | Ignored


@dataclass(frozen=True, slots=True)
class Claimed:
    name: Name
    body: str
    enqueued_at: datetime
    claimed_at: datetime


@dataclass(frozen=True, slots=True)
class Entry:
    name: Name
    state: State
    since: datetime  # 현재 상태에 들어온 시각 (tz-aware UTC). older-than 기준


@dataclass(frozen=True, slots=True)
class StoreInfo:
    """check()의 결과. 저장소가 없으면 exists=False이고 나머지는 None이다."""

    home: Path
    exists: bool
    store: str | None
    store_version: int | None
    min_reader: str | None
    name_rules: int | None


class HomeSource(enum.StrEnum):
    ARGUMENT = "argument"
    PROMPTQ_HOME = "PROMPTQ_HOME"
    XDG_STATE_HOME = "XDG_STATE_HOME"
    DEFAULT = "default"


@dataclass(frozen=True, slots=True)
class HomeResolution:
    path: Path  # 항상 절대 경로
    source: HomeSource

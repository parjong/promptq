"""Value objects. Never imports other promptq modules at runtime."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from promptq.naming import Name, Title


class State(enum.StrEnum):
    PENDING = "pending"
    CLAIMED = "claimed"


@dataclass(frozen=True, slots=True)
class Enqueued:
    name: Name
    enqueued: Literal[True] = True


@dataclass(frozen=True, slots=True)
class Ignored:
    """Ignored because the same name already exists."""

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
    title: Title | None = None


@dataclass(frozen=True, slots=True)
class Entry:
    name: Name
    state: State
    since: datetime  # When it entered its current state (tz-aware UTC); the basis of older-than
    title: Title | None = None


@dataclass(frozen=True, slots=True)
class StoreInfo:
    """Result of check(). If the store does not exist, exists is False and the rest is None."""

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
    path: Path  # always absolute
    source: HomeSource

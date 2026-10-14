"""on-dup policies (internal strategy objects, D6). The public type is Literal["ignore"]."""

from __future__ import annotations

from typing import Protocol

from promptq.models import EnqueueResult, Ignored, State
from promptq.naming import Name


class DupPolicy(Protocol):
    def on_duplicate(self, name: Name, existing_state: State) -> EnqueueResult: ...


class IgnorePolicy:
    def on_duplicate(self, name: Name, existing_state: State) -> EnqueueResult:
        return Ignored(name, existing_state)


_POLICIES: dict[str, DupPolicy] = {"ignore": IgnorePolicy()}


def resolve_policy(on_dup: str) -> DupPolicy:
    try:
        return _POLICIES[on_dup]
    except KeyError:
        raise ValueError(f"unsupported on_dup: {on_dup!r}") from None

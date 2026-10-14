"""Selectors (07, 10). Each term kind is registered and declares a cost grade."""

from __future__ import annotations

import enum
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, ClassVar

from promptq.errors import InvalidName, InvalidSelector
from promptq.models import State
from promptq.naming import Prefix

if TYPE_CHECKING:
    from promptq.naming import Name


class Cost(enum.IntEnum):
    """Cost grade of the information a term needs. has/claim-one allow NAME only (X4)."""

    NAME = 0
    STAT = 1
    RECORD = 2
    PROBE = 3


class EntryView:
    """Read-only view used when a term is evaluated. `since` is only loaded on access."""

    __slots__ = ("_load_since", "_since", "name", "state")

    def __init__(self, name: Name, state: State, load_since: Callable[[], datetime]) -> None:
        self.name = name
        self.state = state
        self._load_since = load_since
        self._since: datetime | None = None

    @property
    def since(self) -> datetime:
        if self._since is None:
            self._since = self._load_since()
        return self._since

    @property
    def claim_record(self) -> None:
        """Phase 1 has no owner sidecar (10)."""
        return None


@dataclass(frozen=True, slots=True)
class PrefixTerm:
    kind: ClassVar[str] = "prefix"
    cost: ClassVar[Cost] = Cost.NAME
    prefix: Prefix

    def matches(self, view: EntryView, now: datetime) -> bool:
        return view.name.startswith(self.prefix)


@dataclass(frozen=True, slots=True)
class StateTerm:
    kind: ClassVar[str] = "state"
    cost: ClassVar[Cost] = Cost.STAT
    state: State

    def matches(self, view: EntryView, now: datetime) -> bool:
        return view.state is self.state


@dataclass(frozen=True, slots=True)
class OlderThanTerm:
    kind: ClassVar[str] = "older-than"
    cost: ClassVar[Cost] = Cost.STAT
    delta: timedelta

    def matches(self, view: EntryView, now: datetime) -> bool:
        return now - view.since > self.delta


Term = PrefixTerm | StateTerm | OlderThanTerm

_DURATION = re.compile(r"(\d+)([smhd])")
_UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}


def parse_duration(text: str) -> timedelta:
    """Formats like `30m`, `6h`, `1d`. The unit is required and the value must be positive."""
    match = _DURATION.fullmatch(text)
    if match is None:
        raise InvalidSelector(f"duration must look like 30m, 6h, or 1d: {text!r}")
    try:
        delta = timedelta(**{_UNITS[match[2]]: int(match[1])})
    except OverflowError:
        raise InvalidSelector(f"duration is too large: {text!r}") from None
    if delta <= timedelta(0):
        raise InvalidSelector(f"duration must be greater than zero: {text!r}")
    return delta


def _parse_prefix(value: str) -> Term:
    try:
        return PrefixTerm(Prefix(value))
    except InvalidName as exc:
        raise InvalidSelector(str(exc)) from exc


def _parse_state(value: str) -> Term:
    try:
        return StateTerm(State(value))
    except ValueError:
        raise InvalidSelector(f"state must be pending or claimed: {value!r}") from None


def _parse_older_than(value: str) -> Term:
    return OlderThanTerm(parse_duration(value))


_PARSERS: dict[str, Callable[[str], Term]] = {
    "prefix": _parse_prefix,
    "state": _parse_state,
    "older-than": _parse_older_than,
}
_RESERVED = frozenset({"regex"})


@dataclass(frozen=True, slots=True)
class Selector:
    """Immutable value object. Combine with `&` (AND). The internal representation is private."""

    _terms: tuple[Term, ...] = ()

    @classmethod
    def prefix(cls, value: str) -> Selector:
        return cls((_parse_prefix(value),))

    @classmethod
    def regex(cls, pattern: str) -> Selector:
        raise NotImplementedError("regex selectors are reserved but not implemented yet")

    @classmethod
    def state(cls, value: State) -> Selector:
        return cls((StateTerm(State(value)),))

    @classmethod
    def older_than(cls, delta: timedelta | str) -> Selector:
        if isinstance(delta, str):
            return cls((OlderThanTerm(parse_duration(delta)),))
        if delta <= timedelta(0):
            raise InvalidSelector(f"duration must be greater than zero: {delta!r}")
        return cls((OlderThanTerm(delta),))

    @classmethod
    def parse(cls, text: str) -> Selector:
        """Parse the CLI form `kind:value`."""
        kind, sep, value = text.partition(":")
        if not sep:
            raise InvalidSelector(f"selector must look like 'kind:value': {text!r}")
        if kind in _RESERVED:
            raise InvalidSelector(f"{kind}: selectors are not supported yet")
        parser = _PARSERS.get(kind)
        if parser is None:
            raise InvalidSelector(f"unknown selector kind: {kind!r}")
        return cls((parser(value),))

    def __and__(self, other: Selector) -> Selector:
        return Selector(self._terms + other._terms)

    def matches(self, view: EntryView, now: datetime) -> bool:
        """Evaluate the cheapest terms first (10)."""
        return all(term.matches(view, now) for term in sorted(self._terms, key=_cost_of))

    @property
    def scan_prefix(self) -> str:
        """Longest prefix, used to narrow the scan. Empty string if there is none."""
        prefixes = [t.prefix for t in self._terms if isinstance(t, PrefixTerm)]
        return max(prefixes, key=len, default="")

    def require_max_cost(self, limit: Cost, *, command: str) -> None:
        """Raise InvalidSelector if a term exceeds the cost grade the command allows."""
        for term in self._terms:
            if term.cost > limit:
                raise InvalidSelector(f"{command} does not accept {term.kind}: selectors")

    def require_prunable(self) -> None:
        """prune-claimed rules (07): older-than is required, state:pending is forbidden."""
        if not any(isinstance(t, OlderThanTerm) for t in self._terms):
            raise InvalidSelector("prune-claimed requires an older-than: selector")
        for term in self._terms:
            if isinstance(term, StateTerm) and term.state is not State.CLAIMED:
                raise InvalidSelector("prune-claimed only targets claimed prompts")


def _cost_of(term: Term) -> Cost:
    return term.cost

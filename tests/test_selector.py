from datetime import UTC, datetime, timedelta

import pytest

from promptq.errors import InvalidSelector
from promptq.models import State
from promptq.naming import Name
from promptq.selector import Cost, EntryView, Selector

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=UTC)


def view(
    name: str = "a/b/1", state: State = State.PENDING, age: timedelta = timedelta(0)
) -> EntryView:
    return EntryView(Name(name), state, lambda: NOW - age)


def test_prefix_is_literal() -> None:
    sel = Selector.parse("prefix:GITHUB/o/foo/")
    assert sel.matches(view("GITHUB/o/foo/X/1"), NOW)
    assert not sel.matches(view("GITHUB/o/foo.bar/X/1"), NOW)


def test_partial_prefix() -> None:
    assert Selector.parse("prefix:GITHUB/o/fo").matches(view("GITHUB/o/foo/X/1"), NOW)


def test_and_combination() -> None:
    sel = Selector.parse("prefix:a/") & Selector.parse("state:claimed")
    assert sel.matches(view("a/b/1", State.CLAIMED), NOW)
    assert not sel.matches(view("a/b/1", State.PENDING), NOW)


def test_older_than() -> None:
    sel = Selector.older_than("6h")
    assert sel.matches(view(age=timedelta(hours=7)), NOW)
    assert not sel.matches(view(age=timedelta(hours=5)), NOW)


def test_since_is_lazy() -> None:
    calls: list[int] = []

    def load() -> datetime:
        calls.append(1)
        return NOW

    v = EntryView(Name("a/1"), State.PENDING, load)
    Selector.parse("prefix:a/").matches(v, NOW)
    assert calls == []


@pytest.mark.parametrize("text", ["30", "0s", "0m", "-1h", "1w", "h", "1.5h", "6H", ""])
def test_invalid_durations(text: str) -> None:
    with pytest.raises(InvalidSelector):
        Selector.parse(f"older-than:{text}")


@pytest.mark.parametrize("text", ["prefix", "regex:a.*", "owner:dead", "state:done", "prefix:a b"])
def test_invalid_selectors(text: str) -> None:
    with pytest.raises(InvalidSelector):
        Selector.parse(text)


def test_regex_factory_is_reserved() -> None:
    with pytest.raises(NotImplementedError):
        Selector.regex(".*")


def test_cost_grades_gate_commands() -> None:
    Selector.parse("prefix:a/").require_max_cost(Cost.NAME, command="has")
    for text in ("state:claimed", "older-than:1h"):
        with pytest.raises(InvalidSelector):
            Selector.parse(text).require_max_cost(Cost.NAME, command="has")


def test_prunable_rules() -> None:
    (Selector.parse("older-than:1h") & Selector.parse("state:claimed")).require_prunable()
    with pytest.raises(InvalidSelector):
        Selector.parse("prefix:a/").require_prunable()
    with pytest.raises(InvalidSelector):
        (Selector.parse("older-than:1h") & Selector.parse("state:pending")).require_prunable()

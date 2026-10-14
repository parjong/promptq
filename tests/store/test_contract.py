"""Store contract tests: every implementation must behave the same way (D16)."""

from datetime import timedelta
from pathlib import Path

import pytest

from promptq.errors import NameConflict
from promptq.models import Claimed, Enqueued, Ignored, State
from promptq.naming import Name
from promptq.selector import Selector
from promptq.store.base import Store
from tests.store.conftest import age

ALL = Selector.parse("prefix:a/")


def enq(store: Store, name: str, body: str = "x") -> None:
    assert isinstance(store.enqueue(Name(name), body, "ignore"), Enqueued)


def test_enqueue_claim_dequeue_roundtrip(store: Store) -> None:
    enq(store, "a/b/1", "안녕\n본문")
    assert store.has(ALL)
    claimed = store.claim_one(ALL)
    assert isinstance(claimed, Claimed)
    assert (claimed.name, claimed.body) == ("a/b/1", "안녕\n본문")
    assert claimed.claimed_at >= claimed.enqueued_at
    assert not store.has(ALL)
    assert store.dequeue(Name("a/b/1")) is True
    assert store.dequeue(Name("a/b/1")) is False


def test_duplicate_enqueue_is_ignored_in_both_states(store: Store) -> None:
    enq(store, "a/1")
    again = store.enqueue(Name("a/1"), "other", "ignore")
    assert again == Ignored(Name("a/1"), State.PENDING)
    store.claim_one(ALL)
    again = store.enqueue(Name("a/1"), "other", "ignore")
    assert again == Ignored(Name("a/1"), State.CLAIMED)


def test_claim_is_fifo(store: Store) -> None:
    for name in ("a/z", "a/m", "a/b"):
        enq(store, name)
    order = [c.name for c in iter(lambda: store.claim_one(ALL), None)]
    assert order == ["a/z", "a/m", "a/b"]


def test_claim_respects_prefix(store: Store) -> None:
    enq(store, "a/foo/1")
    enq(store, "a/foo.bar/1")
    claimed = store.claim_one(Selector.parse("prefix:a/foo/"))
    assert claimed is not None
    assert claimed.name == "a/foo/1"
    assert store.claim_one(Selector.parse("prefix:a/foo/")) is None


def test_claim_empty_returns_none(store: Store) -> None:
    assert store.claim_one(ALL) is None


def test_release_returns_item_to_pending(store: Store) -> None:
    enq(store, "a/1")
    store.claim_one(ALL)
    assert store.release(Name("a/1")) is True
    assert store.release(Name("a/1")) is False
    assert store.has(ALL)


def test_name_must_be_leaf(store: Store) -> None:
    enq(store, "a/b")
    with pytest.raises(NameConflict):
        store.enqueue(Name("a/b/1"), "x", "ignore")
    enq(store, "a/c/1")
    with pytest.raises(NameConflict):
        store.enqueue(Name("a/c"), "x", "ignore")


def test_empty_directories_are_cleaned(store: Store) -> None:
    enq(store, "a/b/c/1")
    store.claim_one(ALL)
    store.dequeue(Name("a/b/c/1"))
    enq(store, "a/b")  # a former parent path can become a leaf again


def test_entries_and_selectors(store: Store) -> None:
    enq(store, "a/1")
    enq(store, "a/2")
    store.claim_one(Selector.parse("prefix:a/1"))
    entries = store.entries(None)
    assert [(e.name, e.state) for e in entries] == [
        ("a/1", State.CLAIMED),
        ("a/2", State.PENDING),
    ]
    claimed_only = store.entries(Selector.parse("state:claimed"))
    assert [e.name for e in claimed_only] == ["a/1"]


def test_prune_claimed_only_removes_old_claimed(store: Store, home: Path) -> None:
    for n in ("a/old", "a/new", "a/pending"):
        enq(store, n)
    store.claim_one(Selector.parse("prefix:a/old"))
    store.claim_one(Selector.parse("prefix:a/new"))
    age(home / "claimed" / "a" / "old", timedelta(hours=7))
    pruned = store.prune_claimed(Selector.parse("older-than:6h") & Selector.parse("prefix:a/"))
    assert pruned == ["a/old"]
    assert {(e.name, e.state) for e in store.entries(None)} == {
        ("a/new", State.CLAIMED),
        ("a/pending", State.PENDING),
    }


def test_claim_refreshes_claim_time(store: Store, home: Path) -> None:
    """An item enqueued long ago must not be prunable right after being claimed (D4)."""
    enq(store, "a/1")
    age(home / "pending" / "a" / "1", timedelta(days=2))
    store.claim_one(ALL)
    assert store.prune_claimed(Selector.parse("older-than:1h")) == []

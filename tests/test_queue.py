from datetime import timedelta
from pathlib import Path

import pytest

from promptq.errors import (
    BodyTooLarge,
    InvalidName,
    InvalidSelector,
    StoreError,
)
from promptq.models import Enqueued, Ignored, State
from promptq.naming import Name
from promptq.queue import MAX_BODY_BYTES, Queue
from promptq.selector import Selector
from promptq.store.directory import DirectoryStore
from tests.store.conftest import age

PREFIX = Selector.prefix("GITHUB/o/r/")
NAME = "GITHUB/o/r/RESOLVE_PR_CONFLICT/1"


@pytest.fixture
def queue(tmp_path: Path) -> Queue:
    return Queue(tmp_path / "home")


def test_construction_does_no_io(tmp_path: Path) -> None:
    Queue(tmp_path / "home")
    assert not (tmp_path / "home").exists()


def test_roundtrip(queue: Queue) -> None:
    assert queue.enqueue(NAME, "do it", on_dup="ignore") == Enqueued(Name(NAME))
    assert queue.has(PREFIX)
    claimed = queue.claim_one(PREFIX)
    assert claimed is not None
    assert (claimed.name, claimed.body) == (NAME, "do it")
    assert not queue.has(PREFIX)
    assert queue.dequeue(NAME) is True
    assert queue.dequeue(NAME) is False


def test_duplicate_enqueue_reports_existing_state(queue: Queue) -> None:
    queue.enqueue(NAME, "a", on_dup="ignore")
    result = queue.enqueue(NAME, "b", on_dup="ignore")
    assert isinstance(result, Ignored)
    assert result.existing_state is State.PENDING


def test_invalid_name_and_oversized_body(queue: Queue) -> None:
    with pytest.raises(InvalidName):
        queue.enqueue("bad name", "x", on_dup="ignore")
    with pytest.raises(BodyTooLarge):
        queue.enqueue(NAME, "x" * (MAX_BODY_BYTES + 1), on_dup="ignore")
    assert not queue.has(PREFIX)


def test_has_and_claim_one_only_take_cheap_selectors(queue: Queue) -> None:
    for selector in (Selector.state(State.PENDING), Selector.older_than("1h")):
        with pytest.raises(InvalidSelector):
            queue.has(selector)
        with pytest.raises(InvalidSelector):
            queue.claim_one(selector)


def test_read_operations_never_create_the_store(tmp_path: Path) -> None:
    q = Queue(tmp_path / "home")
    assert not q.has(PREFIX)
    assert q.list() == []
    assert q.dequeue(NAME) is False
    assert not (tmp_path / "home").exists()


def test_check_reports_a_missing_store_without_creating_it(tmp_path: Path) -> None:
    info = Queue(tmp_path / "home").check()
    assert info.exists is False
    assert not (tmp_path / "home").exists()


def test_check_true_fails_fast_on_foreign_content(tmp_path: Path) -> None:
    (tmp_path / "home").mkdir()
    (tmp_path / "home" / "other.txt").write_text("x")
    with pytest.raises(StoreError):
        Queue(tmp_path / "home", check=True)


def test_create_false_refuses_to_create(tmp_path: Path) -> None:
    q = Queue(tmp_path / "home", create=False)
    with pytest.raises(StoreError):
        q.enqueue(NAME, "x", on_dup="ignore")
    assert not (tmp_path / "home").exists()


def test_list_combines_selectors_with_and(queue: Queue) -> None:
    queue.enqueue("a/1", "x", on_dup="ignore")
    queue.enqueue("a/2", "x", on_dup="ignore")
    queue.claim_one(Selector.prefix("a/1"))
    both = queue.list(Selector.prefix("a/"), Selector.state(State.CLAIMED))
    assert [e.name for e in both] == ["a/1"]
    assert [e.name for e in queue.list()] == ["a/1", "a/2"]


def test_prune_claimed_rules_and_dry_run(tmp_path: Path) -> None:
    q = Queue(tmp_path / "home")
    q.enqueue("a/old", "x", on_dup="ignore")
    q.enqueue("a/pending", "x", on_dup="ignore")
    q.claim_one(Selector.prefix("a/old"))
    age(tmp_path / "home" / "claimed" / "a" / "old", timedelta(hours=7))

    with pytest.raises(InvalidSelector):
        q.prune_claimed(Selector.prefix("a/"))  # older-than is required
    with pytest.raises(InvalidSelector):
        q.prune_claimed(Selector.older_than("1h"), Selector.state(State.PENDING))

    older = Selector.older_than("6h")
    assert q.prune_claimed(older, dry_run=True) == ["a/old"]
    assert [e.name for e in q.list(Selector.state(State.CLAIMED))] == ["a/old"]  # still there
    assert q.prune_claimed(older) == ["a/old"]
    assert [e.name for e in q.list()] == ["a/pending"]


def test_release_returns_an_item(queue: Queue) -> None:
    queue.enqueue(NAME, "x", on_dup="ignore")
    queue.claim_one(PREFIX)
    assert queue.release(NAME) is True
    assert queue.release(NAME) is False
    assert queue.has(PREFIX)


def test_store_injection_and_context_manager(tmp_path: Path) -> None:
    store = DirectoryStore(tmp_path / "injected", create=True)
    with Queue(tmp_path / "ignored", store=store) as q:
        q.enqueue(NAME, "x", on_dup="ignore")
    assert (tmp_path / "injected" / "pending").exists()
    assert not (tmp_path / "ignored").exists()

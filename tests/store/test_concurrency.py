"""Multi-process tests for the atomicity guarantees of link/rename (03, 04)."""

import multiprocessing as mp
from pathlib import Path

from promptq.models import Enqueued
from promptq.naming import Name
from promptq.selector import Selector
from promptq.store.directory import DirectoryStore

PROCESSES = 8
ITEMS = 60


def _enqueue_same(store_dir: str, barrier: "mp.synchronize.Barrier", out: "mp.Queue[bool]") -> None:
    store = DirectoryStore(Path(store_dir), create=True)
    barrier.wait()
    out.put(isinstance(store.enqueue(Name("a/same"), "x", "ignore"), Enqueued))


def _claim_all(
    store_dir: str, barrier: "mp.synchronize.Barrier", out: "mp.Queue[list[str]]"
) -> None:
    store = DirectoryStore(Path(store_dir), create=True)
    selector = Selector.parse("prefix:a/")
    got: list[str] = []
    barrier.wait()
    while (claimed := store.claim_one(selector)) is not None:
        got.append(str(claimed.name))
    out.put(got)


def test_concurrent_enqueue_of_same_name_has_exactly_one_winner(tmp_path: Path) -> None:
    ctx = mp.get_context("fork")
    barrier = ctx.Barrier(PROCESSES)
    out: mp.Queue[bool] = ctx.Queue()
    # Initialize first so the race is on `link`, not on manifest creation.
    DirectoryStore(tmp_path / "h", create=True).enqueue(Name("a/seed"), "x", "ignore")
    procs = [
        ctx.Process(target=_enqueue_same, args=(str(tmp_path / "h"), barrier, out))
        for _ in range(PROCESSES)
    ]
    for p in procs:
        p.start()
    results = [out.get(timeout=30) for _ in procs]
    for p in procs:
        p.join(timeout=30)
    assert results.count(True) == 1


def test_concurrent_claim_gives_each_item_to_exactly_one_process(tmp_path: Path) -> None:
    store_dir = tmp_path / "h"
    store = DirectoryStore(store_dir, create=True)
    names = {f"a/{i:03d}" for i in range(ITEMS)}
    for n in names:
        store.enqueue(Name(n), "x", "ignore")

    ctx = mp.get_context("fork")
    barrier = ctx.Barrier(PROCESSES)
    out: mp.Queue[list[str]] = ctx.Queue()
    procs = [
        ctx.Process(target=_claim_all, args=(str(store_dir), barrier, out))
        for _ in range(PROCESSES)
    ]
    for p in procs:
        p.start()
    batches = [out.get(timeout=60) for _ in procs]
    for p in procs:
        p.join(timeout=60)

    all_claimed = [n for batch in batches for n in batch]
    assert len(all_claimed) == len(set(all_claimed))  # nobody got the same item twice
    assert set(all_claimed) == names  # nothing was lost

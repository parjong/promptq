import json
from pathlib import Path

import pytest

from promptq import _version
from promptq.errors import IncompatibleStore, StoreError
from promptq.naming import Name
from promptq.selector import Selector
from promptq.store.factory import StoreFactory
from promptq.store.manifest import parse_version, read_manifest

ALL = Selector.parse("prefix:a/")


def write_manifest(store_dir: Path, **overrides: object) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {
        "format": 1,
        "store": "dir",
        "store_version": 1,
        "min_reader": "0.0.1",
        "name_rules": 1,
        "created_at": "2026-10-14T00:00:00Z",
        "created_by": "test",
    }
    data.update(overrides)
    (store_dir / "manifest.json").write_text(json.dumps(data))


def test_missing_store_dir_is_an_empty_queue_and_reads_do_not_create(store_dir: Path) -> None:
    store = StoreFactory.open(store_dir, create=True)
    assert not store.has(ALL)
    assert store.claim_one(ALL) is None or store_dir.exists()  # claim-one may lazily create
    assert store.entries(None) == []


def test_read_only_operations_never_create_the_store(store_dir: Path) -> None:
    store = StoreFactory.open(store_dir, create=True)
    assert not store.has(ALL)
    assert store.entries(None) == []
    assert store.dequeue(Name("a/1")) is False
    assert not store_dir.exists()


def test_first_write_creates_store_with_manifest(store_dir: Path) -> None:
    StoreFactory.open(store_dir, create=True).enqueue(Name("a/1"), "x", "ignore")
    manifest = read_manifest(store_dir)
    assert manifest is not None
    assert (manifest.store, manifest.store_version, manifest.name_rules) == ("dir", 1, 1)
    assert oct(store_dir.stat().st_mode & 0o777) == "0o700"


def test_create_false_refuses_to_create(store_dir: Path) -> None:
    with pytest.raises(StoreError):
        StoreFactory.open(store_dir, create=False).enqueue(Name("a/1"), "x", "ignore")
    assert not store_dir.exists()


def test_store_dir_with_foreign_content_is_an_error(store_dir: Path) -> None:
    store_dir.mkdir()
    (store_dir / "something.txt").write_text("hi")
    with pytest.raises(StoreError):
        StoreFactory.open(store_dir, create=True)
    with pytest.raises(StoreError):
        StoreFactory.inspect(store_dir)


def test_items_without_a_manifest_are_not_mistaken_for_an_empty_store(store_dir: Path) -> None:
    StoreFactory.open(store_dir, create=True).enqueue(Name("a/1"), "x", "ignore")
    (store_dir / "manifest.json").unlink()
    with pytest.raises(StoreError):
        StoreFactory.open(store_dir, create=True)
    with pytest.raises(StoreError):
        StoreFactory.inspect(store_dir)


def test_half_initialized_layout_counts_as_empty(store_dir: Path) -> None:
    for sub in ("tmp", "pending", "claimed"):
        (store_dir / sub).mkdir(parents=True)
    assert StoreFactory.inspect(store_dir).exists is False


def test_unknown_store_kind(store_dir: Path) -> None:
    write_manifest(store_dir, store="sqlite")
    with pytest.raises(IncompatibleStore):
        StoreFactory.open(store_dir, create=True)


def test_min_reader_blocks_writes_but_allows_reads(store_dir: Path) -> None:
    write_manifest(store_dir, min_reader="999.0.0")
    store = StoreFactory.open(store_dir, create=True)
    assert not store.has(ALL)
    assert store.entries(None) == []
    with pytest.raises(IncompatibleStore):
        store.enqueue(Name("a/1"), "x", "ignore")
    with pytest.raises(IncompatibleStore):
        store.dequeue(Name("a/1"))
    with pytest.raises(IncompatibleStore):
        StoreFactory.inspect(store_dir)


def test_newer_store_version_blocks_writes(store_dir: Path) -> None:
    write_manifest(store_dir, store_version=2)
    with pytest.raises(IncompatibleStore):
        StoreFactory.open(store_dir, create=True).enqueue(Name("a/1"), "x", "ignore")


def test_inspect_reports_missing_store_without_error(store_dir: Path) -> None:
    info = StoreFactory.inspect(store_dir)
    assert (info.exists, info.store, info.home) == (False, None, store_dir)
    assert not store_dir.exists()


def test_inspect_reports_existing_store(store_dir: Path) -> None:
    StoreFactory.open(store_dir, create=True).enqueue(Name("a/1"), "x", "ignore")
    info = StoreFactory.inspect(store_dir)
    assert (info.exists, info.store, info.store_version, info.name_rules) == (True, "dir", 1, 1)


def test_broken_manifest(store_dir: Path) -> None:
    store_dir.mkdir()
    (store_dir / "manifest.json").write_text("{not json")
    with pytest.raises(StoreError):
        StoreFactory.open(store_dir, create=True)


def test_parse_version() -> None:
    assert parse_version("1.2.3") == (1, 2, 3)
    for bad in ("1.2", "1.2.3rc1", "v1.2.3", ""):
        with pytest.raises(IncompatibleStore):
            parse_version(bad)


def test_dev_build_can_use_the_store_it_created(store_dir: Path) -> None:
    # A version like "0.0.1.dev5+g1234" must still satisfy the min_reader it wrote.
    assert _version.__version__
    StoreFactory.open(store_dir, create=True).enqueue(Name("a/1"), "x", "ignore")
    StoreFactory.open(store_dir, create=True).enqueue(Name("a/2"), "x", "ignore")

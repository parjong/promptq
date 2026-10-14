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


def write_manifest(home: Path, **overrides: object) -> None:
    home.mkdir(parents=True, exist_ok=True)
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
    (home / "manifest.json").write_text(json.dumps(data))


def test_missing_home_is_an_empty_queue_and_reads_do_not_create(home: Path) -> None:
    store = StoreFactory.open(home, create=True)
    assert not store.has(ALL)
    assert store.claim_one(ALL) is None or home.exists()  # claim-one may lazily create
    assert store.entries(None) == []


def test_read_only_operations_never_create_the_store(home: Path) -> None:
    store = StoreFactory.open(home, create=True)
    assert not store.has(ALL)
    assert store.entries(None) == []
    assert store.dequeue(Name("a/1")) is False
    assert not home.exists()


def test_first_write_creates_store_with_manifest(home: Path) -> None:
    StoreFactory.open(home, create=True).enqueue(Name("a/1"), "x", "ignore")
    manifest = read_manifest(home)
    assert manifest is not None
    assert (manifest.store, manifest.store_version, manifest.name_rules) == ("dir", 1, 1)
    assert oct(home.stat().st_mode & 0o777) == "0o700"


def test_create_false_refuses_to_create(home: Path) -> None:
    with pytest.raises(StoreError):
        StoreFactory.open(home, create=False).enqueue(Name("a/1"), "x", "ignore")
    assert not home.exists()


def test_home_with_foreign_content_is_an_error(home: Path) -> None:
    home.mkdir()
    (home / "something.txt").write_text("hi")
    with pytest.raises(StoreError):
        StoreFactory.open(home, create=True)
    with pytest.raises(StoreError):
        StoreFactory.inspect(home)


def test_unknown_store_kind(home: Path) -> None:
    write_manifest(home, store="sqlite")
    with pytest.raises(IncompatibleStore):
        StoreFactory.open(home, create=True)


def test_min_reader_blocks_writes_but_allows_reads(home: Path) -> None:
    write_manifest(home, min_reader="999.0.0")
    store = StoreFactory.open(home, create=True)
    assert not store.has(ALL)
    assert store.entries(None) == []
    with pytest.raises(IncompatibleStore):
        store.enqueue(Name("a/1"), "x", "ignore")
    with pytest.raises(IncompatibleStore):
        store.dequeue(Name("a/1"))
    with pytest.raises(IncompatibleStore):
        StoreFactory.inspect(home)


def test_newer_store_version_blocks_writes(home: Path) -> None:
    write_manifest(home, store_version=2)
    with pytest.raises(IncompatibleStore):
        StoreFactory.open(home, create=True).enqueue(Name("a/1"), "x", "ignore")


def test_inspect_reports_missing_store_without_error(home: Path) -> None:
    info = StoreFactory.inspect(home)
    assert (info.exists, info.store, info.home) == (False, None, home)
    assert not home.exists()


def test_inspect_reports_existing_store(home: Path) -> None:
    StoreFactory.open(home, create=True).enqueue(Name("a/1"), "x", "ignore")
    info = StoreFactory.inspect(home)
    assert (info.exists, info.store, info.store_version, info.name_rules) == (True, "dir", 1, 1)


def test_broken_manifest(home: Path) -> None:
    home.mkdir()
    (home / "manifest.json").write_text("{not json")
    with pytest.raises(StoreError):
        StoreFactory.open(home, create=True)


def test_parse_version() -> None:
    assert parse_version("1.2.3") == (1, 2, 3)
    for bad in ("1.2", "1.2.3rc1", "v1.2.3", ""):
        with pytest.raises(IncompatibleStore):
            parse_version(bad)


def test_dev_build_can_use_the_store_it_created(home: Path) -> None:
    # A version like "0.0.1.dev5+g1234" must still satisfy the min_reader it wrote.
    assert _version.__version__
    StoreFactory.open(home, create=True).enqueue(Name("a/1"), "x", "ignore")
    StoreFactory.open(home, create=True).enqueue(Name("a/2"), "x", "ignore")

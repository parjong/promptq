import json
from dataclasses import replace
from pathlib import Path

import pytest

from promptq.errors import IncompatibleStore, StoreError
from promptq.store import manifest as m


def test_publish_is_won_by_exactly_one_writer(tmp_path: Path) -> None:
    first = m.new_manifest("dir", 1)
    assert m.publish_manifest(tmp_path, first) is True
    assert m.publish_manifest(tmp_path, replace(first, store="sqlite")) is False
    stored = m.read_manifest(tmp_path)
    assert stored is not None
    assert stored.store == "dir"
    assert list(tmp_path.glob(".manifest-*")) == []  # temp files are cleaned up


def test_read_missing_manifest_is_none(tmp_path: Path) -> None:
    assert m.read_manifest(tmp_path) is None


@pytest.mark.parametrize("content", ["{not json", "[]", '{"format": 1}'])
def test_read_broken_manifest(tmp_path: Path, content: str) -> None:
    (tmp_path / m.MANIFEST_NAME).write_text(content)
    with pytest.raises(StoreError):
        m.read_manifest(tmp_path)


def test_read_unknown_format(tmp_path: Path) -> None:
    m.publish_manifest(tmp_path, replace(m.new_manifest("dir", 1), format=99))
    with pytest.raises(IncompatibleStore):
        m.read_manifest(tmp_path)


def test_manifest_round_trip_keeps_features(tmp_path: Path) -> None:
    m.publish_manifest(tmp_path, replace(m.new_manifest("dir", 1), features=("x",)))
    stored = m.read_manifest(tmp_path)
    assert stored is not None
    assert stored.features == ("x",)
    assert json.loads((tmp_path / m.MANIFEST_NAME).read_text())["features"] == ["x"]


def test_parse_version() -> None:
    assert m.parse_version("1.2.3") == (1, 2, 3)
    for bad in ("1.2", "1.2.3rc1", "v1.2.3", ""):
        with pytest.raises(IncompatibleStore):
            m.parse_version(bad)


@pytest.mark.parametrize(
    ("installed", "expected"),
    [("1.2.3", (1, 2, 3)), ("0.0.1.dev5+g1234.d20261014", (0, 0, 1)), ("2", (2, 0, 0))],
)
def test_installed_version_reads_leading_numbers(
    monkeypatch: pytest.MonkeyPatch, installed: str, expected: tuple[int, int, int]
) -> None:
    monkeypatch.setattr(m, "__version__", installed)
    assert m.installed_version() == expected


def test_min_reader_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(m, "__version__", "0.2.0")
    base = m.new_manifest("dir", 1)
    assert not m.min_reader_exceeded(replace(base, min_reader="0.2.0"))
    assert m.min_reader_exceeded(replace(base, min_reader="0.2.1"))
    assert not m.min_reader_exceeded(replace(base, min_reader="0.1.9"))
    # A dev build must satisfy the min_reader it wrote itself.
    monkeypatch.setattr(m, "__version__", "0.0.1.dev5+gabc")
    assert not m.min_reader_exceeded(base)

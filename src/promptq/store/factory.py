"""StoreFactory: picks the Store implementation, treating the manifest as the single truth (05)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from promptq.errors import IncompatibleStore, StoreError
from promptq.models import StoreInfo
from promptq.store.base import Store
from promptq.store.directory import STORE_KIND, STORE_VERSION, DirectoryStore
from promptq.store.manifest import NAME_RULES, Manifest, min_reader_exceeded, read_manifest

_LAYOUT_DIRS = frozenset({"tmp", "pending", "claimed"})


@dataclass(frozen=True, slots=True)
class _Spec:
    store_version: int
    build: Callable[[Path, bool, IncompatibleStore | None], Store]


_REGISTRY: dict[str, _Spec] = {
    STORE_KIND: _Spec(
        STORE_VERSION,
        lambda home, create, blocked: DirectoryStore(home, create=create, write_blocked=blocked),
    ),
}


def _is_empty(home: Path) -> bool:
    """A store is empty if absent, empty, or holding only empty layout dirs (half-done init)."""
    if not home.exists():
        return True
    if not home.is_dir():
        return False
    return all(
        child.name in _LAYOUT_DIRS and child.is_dir() and not any(child.iterdir())
        for child in home.iterdir()
    )


def _write_block_reason(manifest: Manifest, spec: _Spec) -> str | None:
    if min_reader_exceeded(manifest):
        return f"this store needs promptq {manifest.min_reader} or newer; please upgrade"
    if manifest.store_version > spec.store_version:
        return f"store version {manifest.store_version} is newer than this promptq; please upgrade"
    if manifest.name_rules != NAME_RULES:
        return f"name rules version {manifest.name_rules} differs from this promptq; please upgrade"
    return None


def _spec_for(manifest: Manifest) -> _Spec:
    spec = _REGISTRY.get(manifest.store)
    if spec is None:
        raise IncompatibleStore(f"unknown store kind {manifest.store!r}; please upgrade promptq")
    return spec


class StoreFactory:
    @staticmethod
    def open(home: Path, *, create: bool) -> Store:
        """Write-only incompatibilities (e.g. min_reader) raise from the Store on write."""
        manifest = read_manifest(home)
        if manifest is None:
            if not _is_empty(home):
                raise StoreError(f"{home} has content but no manifest (see 'promptq store check')")
            return _REGISTRY[STORE_KIND].build(home, create, None)
        spec = _spec_for(manifest)
        reason = _write_block_reason(manifest, spec)
        return spec.build(home, create, IncompatibleStore(reason) if reason else None)

    @staticmethod
    def inspect(home: Path) -> StoreInfo:
        """Read-only check. A missing store is not an error; only incompatibilities raise."""
        manifest = read_manifest(home)
        if manifest is None:
            if not _is_empty(home):
                raise StoreError(f"{home} has content but no manifest")
            return StoreInfo(home, False, None, None, None, None)
        reason = _write_block_reason(manifest, _spec_for(manifest))
        if reason:
            raise IncompatibleStore(reason)
        return StoreInfo(
            home,
            True,
            manifest.store,
            manifest.store_version,
            manifest.min_reader,
            manifest.name_rules,
        )

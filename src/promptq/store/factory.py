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
    """A store is empty if absent, empty, or holding only layout dirs from a half-done init."""
    if not home.exists():
        return True
    if not home.is_dir():
        return False
    return all(child.name in _LAYOUT_DIRS for child in home.iterdir())


def _write_block_reason(manifest: Manifest, spec: _Spec) -> str | None:
    if min_reader_exceeded(manifest):
        return f"이 저장소는 promptq {manifest.min_reader} 이상이 필요합니다. 업그레이드하세요"
    if manifest.store_version > spec.store_version:
        return f"저장소 버전({manifest.store_version})이 더 새롭습니다. promptq를 업그레이드하세요"
    if manifest.name_rules != NAME_RULES:
        return f"이름 규칙 버전({manifest.name_rules})이 다릅니다. promptq를 업그레이드하세요"
    return None


def _spec_for(manifest: Manifest) -> _Spec:
    spec = _REGISTRY.get(manifest.store)
    if spec is None:
        raise IncompatibleStore(f"이 저장소는 {manifest.store!r}로 만들어졌습니다")
    return spec


class StoreFactory:
    @staticmethod
    def open(home: Path, *, create: bool) -> Store:
        """Write-only incompatibilities (e.g. min_reader) raise from the Store on write."""
        manifest = read_manifest(home)
        if manifest is None:
            if not _is_empty(home):
                raise StoreError(f"{home}에 내용이 있지만 manifest가 없습니다 (store check 참고)")
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
                raise StoreError(f"{home}에 내용이 있지만 manifest가 없습니다")
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

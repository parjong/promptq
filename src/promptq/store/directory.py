"""Directory-based Store (03, 04). Concurrency relies on the atomicity of link and rename."""

from __future__ import annotations

import json
import os
import stat
import time
import uuid
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from promptq.errors import IncompatibleStore, InvalidName, InvalidTitle, NameConflict, StoreError
from promptq.models import Claimed, Enqueued, EnqueueResult, Entry, State
from promptq.naming import Name, Title
from promptq.policy import resolve_policy
from promptq.selector import EntryView, Selector
from promptq.store.manifest import MANIFEST_NAME, new_manifest, publish_manifest, read_manifest

STORE_KIND = "dir"
STORE_VERSION = 1
TMP_MAX_AGE_SECONDS = 3600
_RETRIES = 5
_LAYOUT = ("tmp", "pending", "claimed")


def _utc(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, UTC)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class DirectoryStore:
    kind = STORE_KIND

    def __init__(
        self,
        home: Path,
        *,
        create: bool,
        write_blocked: IncompatibleStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._home = home
        self._create = create
        self._write_blocked = write_blocked
        self._clock = clock or (lambda: datetime.now(UTC))

    # --- initialization ---

    def _initialized(self) -> bool:
        return (self._home / MANIFEST_NAME).exists()

    def _initialize(self) -> None:
        self._home.mkdir(mode=0o700, parents=True, exist_ok=True)
        for sub in _LAYOUT:
            (self._home / sub).mkdir(mode=0o700, exist_ok=True)
        if not publish_manifest(self._home, new_manifest(STORE_KIND, STORE_VERSION)):
            manifest = read_manifest(self._home)
            if manifest is None or manifest.store != STORE_KIND:
                raise IncompatibleStore("the store was created by a different implementation")

    def _check_writable(self) -> None:
        if self._write_blocked is not None:
            raise self._write_blocked

    def _ensure_initialized(self) -> None:
        """Lazily create the store on first write (D15). With create=False, raise instead."""
        self._check_writable()
        if self._initialized():
            return
        if not self._create:
            raise StoreError(f"no store at {self._home}")
        self._initialize()

    # --- paths ---

    def _path(self, state: State, name: str) -> Path:
        return self._home / state.value / name

    def _walk(self, state: State, prefix: str) -> Iterator[tuple[Name, Path]]:
        root = self._home / state.value
        dir_part = prefix.rpartition("/")[0]
        yield from self._walk_dir(root, root / dir_part if dir_part else root, dir_part, prefix)

    def _walk_dir(
        self, root: Path, directory: Path, rel: str, prefix: str
    ) -> Iterator[tuple[Name, Path]]:
        try:
            with os.scandir(directory) as it:
                children = sorted(it, key=lambda e: e.name)
        except (FileNotFoundError, NotADirectoryError):
            return
        for child in children:
            child_rel = f"{rel}/{child.name}" if rel else child.name
            if child.is_dir(follow_symlinks=False):
                boundary = child_rel + "/"
                if boundary.startswith(prefix) or prefix.startswith(boundary):
                    yield from self._walk_dir(root, Path(child.path), child_rel, prefix)
            elif child.is_file(follow_symlinks=False) and child_rel.startswith(prefix):
                try:
                    yield Name(child_rel), Path(child.path)
                except InvalidName:
                    continue  # ignore stray files that did not come from promptq

    def _view(self, name: Name, state: State, path: Path) -> EntryView:
        return EntryView(name, state, lambda: _utc(os.stat(path).st_mtime))

    def _matching(self, state: State, selector: Selector) -> Iterator[tuple[Name, Path]]:
        now = self._clock()
        for name, path in self._walk(state, selector.scan_prefix):
            if selector.matches(self._view(name, state, path), now):
                yield name, path

    def _cleanup_dirs(self, state: State, path: Path) -> None:
        """Remove empty parent directories; stop when one is non-empty or we lose a race."""
        root = self._home / state.value
        parent = path.parent
        while parent != root:
            try:
                parent.rmdir()
            except OSError:
                return
            parent = parent.parent

    # --- envelope ---

    @staticmethod
    def _read_envelope(path: Path) -> tuple[str, datetime, Title | None]:
        """Return (body, enqueued_at, title). The title is optional and absent in older items."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            title = Title(raw["title"]) if raw.get("title") is not None else None
            return str(raw["body"]), datetime.fromisoformat(raw["enqueued_at"]), title
        except FileNotFoundError:
            raise
        except (OSError, ValueError, KeyError, TypeError, InvalidTitle) as exc:
            raise StoreError(f"item file is corrupted: {path}: {exc!r}") from exc

    # --- operations ---

    def _existing_state(self, name: Name) -> State | None:
        for state in (State.PENDING, State.CLAIMED):
            try:
                mode = os.lstat(self._path(state, name)).st_mode
            except FileNotFoundError:
                continue
            except NotADirectoryError:
                raise NameConflict(f"a parent of {name} is already used as a name") from None
            if stat.S_ISDIR(mode):
                raise NameConflict(f"{name} is a parent path of another name")
            return state
        return None

    def _gc_tmp(self) -> None:
        cutoff = time.time() - TMP_MAX_AGE_SECONDS
        try:
            with os.scandir(self._home / "tmp") as it:
                for entry in it:
                    try:
                        if entry.stat().st_mtime < cutoff:
                            os.unlink(entry.path)
                    except OSError:
                        continue
        except OSError:
            return

    def enqueue(
        self, name: Name, body: str, on_dup: Literal["ignore"], title: Title | None = None
    ) -> EnqueueResult:
        policy = resolve_policy(on_dup)
        self._ensure_initialized()
        existing = self._existing_state(name)
        if existing is not None:
            return policy.on_duplicate(name, existing)
        self._gc_tmp()
        envelope = {"v": 1, "name": str(name), "enqueued_at": _iso(self._clock()), "body": body}
        if title is not None:
            envelope["title"] = str(title)
        tmp = self._home / "tmp" / f"{os.getpid()}-{uuid.uuid4().hex}"
        with tmp.open("wb") as f:
            f.write(json.dumps(envelope, ensure_ascii=False).encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        target = self._path(State.PENDING, name)
        try:
            for _ in range(_RETRIES):
                try:
                    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                except (FileExistsError, NotADirectoryError):
                    raise NameConflict(f"a parent of {name} is already used as a name") from None
                try:
                    os.link(tmp, target)
                except FileNotFoundError:
                    continue  # raced with empty-directory cleanup; recreate and retry
                except FileExistsError:
                    if target.is_dir():
                        raise NameConflict(f"{name} is a parent path of another name") from None
                    return policy.on_duplicate(name, self._existing_state(name) or State.PENDING)
                except NotADirectoryError:
                    raise NameConflict(f"a parent of {name} is already used as a name") from None
                return Enqueued(name)
            raise StoreError(f"enqueue kept losing races with directory cleanup: {name}")
        finally:
            tmp.unlink(missing_ok=True)

    def has(self, selector: Selector) -> bool:
        return next(self._matching(State.PENDING, selector), None) is not None

    def claim_one(self, selector: Selector) -> Claimed | None:
        if self._write_blocked is None and not self._initialized() and self._create:
            self._initialize()
        self._check_writable()
        candidates: list[tuple[datetime, str, Name, Path]] = []
        for name, path in self._matching(State.PENDING, selector):
            try:
                _, enqueued_at, _ = self._read_envelope(path)
            except FileNotFoundError:
                continue  # another consumer already took it
            candidates.append((enqueued_at, str(name), name, path))
        candidates.sort(key=lambda c: (c[0], c[1]))
        for _, _, name, src in candidates:
            dst = self._path(State.CLAIMED, name)
            for _ in range(_RETRIES):
                try:
                    os.utime(src)  # start of the claim time; rename preserves mtime (D4)
                    dst.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    os.rename(src, dst)
                except FileNotFoundError:
                    if src.exists():
                        continue  # raced with cleanup of the claimed-side directory
                    break  # another consumer won the race; try the next candidate
                self._cleanup_dirs(State.PENDING, src)
                body, enqueued_at, title = self._read_envelope(dst)
                return Claimed(name, body, enqueued_at, _utc(os.stat(dst).st_mtime), title)
        return None

    def dequeue(self, name: Name) -> bool:
        self._check_writable()
        path = self._path(State.CLAIMED, name)
        try:
            os.unlink(path)
        except (FileNotFoundError, NotADirectoryError, IsADirectoryError):
            return False
        self._cleanup_dirs(State.CLAIMED, path)
        return True

    def release(self, name: Name) -> bool:
        self._check_writable()
        src = self._path(State.CLAIMED, name)
        dst = self._path(State.PENDING, name)
        for _ in range(_RETRIES):
            try:
                dst.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.rename(src, dst)
            except FileNotFoundError:
                if src.exists():
                    continue
                return False
            except NotADirectoryError:
                return False
            self._cleanup_dirs(State.CLAIMED, src)
            return True
        raise StoreError(f"release kept losing races with directory cleanup: {name}")

    def prune_claimed(self, selector: Selector) -> Sequence[Name]:
        self._check_writable()
        pruned: list[Name] = []
        for name, path in list(self._matching(State.CLAIMED, selector)):
            # re-check mtime right before deleting (it may have been released and re-claimed)
            if not selector.matches(self._view(name, State.CLAIMED, path), self._clock()):
                continue
            try:
                os.unlink(path)
            except FileNotFoundError:
                continue  # already dequeued
            self._cleanup_dirs(State.CLAIMED, path)
            pruned.append(name)
        return pruned

    def entries(self, selector: Selector | None) -> Sequence[Entry]:
        selector = selector or Selector()
        result: list[Entry] = []
        for state in (State.PENDING, State.CLAIMED):
            for name, path in self._matching(state, selector):
                try:
                    since = _utc(os.stat(path).st_mtime)
                    title = self._read_envelope(path)[2]
                except FileNotFoundError:
                    continue
                result.append(Entry(name, state, since, title))
        result.sort(key=lambda e: (e.name, e.state))
        return result

    def close(self) -> None:
        return None

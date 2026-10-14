"""Queue: the public facade (09). Validates input and delegates to a Store."""

from __future__ import annotations

from collections.abc import Sequence
from functools import reduce
from pathlib import Path
from types import TracebackType
from typing import Literal, Self

from promptq.errors import BodyTooLarge
from promptq.home import StrPath, resolve_home
from promptq.models import Claimed, EnqueueResult, Entry, HomeResolution, State, StoreInfo
from promptq.naming import Name
from promptq.selector import Cost, Selector
from promptq.store.base import Store
from promptq.store.factory import StoreFactory

MAX_BODY_BYTES = 1024 * 1024


class Queue:
    def __init__(
        self,
        home: StrPath | None = None,
        *,
        create: bool = True,
        check: bool = False,
        store: Store | None = None,
    ) -> None:
        """Create a handle on the queue at `home`.

        Constructing performs no I/O (the store is opened on first use), unless `check=True`,
        which runs check() immediately so incompatibilities surface here. With `store`, the
        given implementation is used as is, bypassing StoreFactory (for tests and injection).
        With `create=False`, write operations refuse to create a missing store.
        """
        self._resolution = resolve_home(home)
        self._create = create
        self._store = store
        if check:
            self.check()

    @property
    def home(self) -> Path:
        return self._resolution.path

    @property
    def home_resolution(self) -> HomeResolution:
        return self._resolution

    def _open(self) -> Store:
        if self._store is None:
            self._store = StoreFactory.open(self.home, create=self._create)
        return self._store

    def check(self) -> StoreInfo:
        """Read the manifest and verify compatibility without creating or changing anything."""
        return StoreFactory.inspect(self.home)

    def close(self) -> None:
        if self._store is not None:
            self._store.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # --- Producer ---

    def enqueue(self, name: str, body: str, *, on_dup: Literal["ignore"]) -> EnqueueResult:
        valid = Name(name)
        size = len(body.encode("utf-8"))
        if size > MAX_BODY_BYTES:
            raise BodyTooLarge(f"body is larger than {MAX_BODY_BYTES} bytes: {size} bytes")
        return self._open().enqueue(valid, body, on_dup)

    def has(self, selector: Selector) -> bool:
        selector.require_max_cost(Cost.NAME, command="has")
        return self._open().has(selector)

    def list(self, *selectors: Selector) -> Sequence[Entry]:
        combined = reduce(lambda a, b: a & b, selectors) if selectors else None
        return self._open().entries(combined)

    def prune_claimed(self, *selectors: Selector, dry_run: bool = False) -> Sequence[Name]:
        combined = reduce(lambda a, b: a & b, selectors, Selector())
        combined.require_prunable()
        target = combined & Selector.state(State.CLAIMED)
        store = self._open()
        if dry_run:
            return [entry.name for entry in store.entries(target)]
        return store.prune_claimed(target)

    # --- Consumer ---

    def claim_one(self, selector: Selector) -> Claimed | None:
        selector.require_max_cost(Cost.NAME, command="claim-one")
        return self._open().claim_one(selector)

    def dequeue(self, name: str) -> bool:
        return self._open().dequeue(Name(name))

    def release(self, name: str) -> bool:
        return self._open().release(Name(name))

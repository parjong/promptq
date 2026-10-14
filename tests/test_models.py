import dataclasses
from datetime import UTC, datetime
from pathlib import Path

import pytest

from promptq.models import (
    Enqueued,
    EnqueueResult,
    Entry,
    HomeResolution,
    HomeSource,
    Ignored,
    State,
    StoreInfo,
)
from promptq.naming import Name


def test_state_values_match_cli_strings() -> None:
    assert State("pending") is State.PENDING
    assert State.CLAIMED.value == "claimed"


def test_enqueue_results_can_be_told_apart() -> None:
    results: list[EnqueueResult] = [Enqueued(Name("a/1")), Ignored(Name("a/1"), State.CLAIMED)]
    kinds = []
    for result in results:
        match result:
            case Enqueued():
                kinds.append("enqueued")
            case Ignored(existing_state=state):
                kinds.append(f"ignored:{state}")
    assert kinds == ["enqueued", "ignored:claimed"]
    assert [r.enqueued for r in results] == [True, False]


def test_values_are_frozen() -> None:
    entry = Entry(Name("a/1"), State.PENDING, datetime(2026, 1, 1, tzinfo=UTC))
    with pytest.raises(dataclasses.FrozenInstanceError):
        entry.state = State.CLAIMED  # type: ignore[misc]


def test_store_info_and_home_resolution() -> None:
    info = StoreInfo(Path("/x"), False, None, None, None, None)
    assert not info.exists
    assert HomeResolution(Path("/x"), HomeSource.DEFAULT).source == "default"

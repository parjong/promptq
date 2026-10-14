import pytest

from promptq.models import Ignored, State
from promptq.naming import Name
from promptq.policy import resolve_policy


def test_ignore_policy_reports_the_existing_state() -> None:
    result = resolve_policy("ignore").on_duplicate(Name("a/1"), State.CLAIMED)
    assert result == Ignored(Name("a/1"), State.CLAIMED)


def test_unknown_policy_is_rejected() -> None:
    with pytest.raises(ValueError):
        resolve_policy("override")

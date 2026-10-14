"""Name validation. Names are validated, never normalized (decision #2)."""

from __future__ import annotations

import re
from typing import Self

from promptq.errors import InvalidName

MAX_SEGMENT_LENGTH = 128
MAX_NAME_LENGTH = 512

_SEGMENT = re.compile(r"[A-Za-z0-9._-]+")


def _check_segments(value: str, *, what: str) -> None:
    if len(value) > MAX_NAME_LENGTH:
        raise InvalidName(f"{what} is longer than {MAX_NAME_LENGTH} characters: {len(value)}")
    for segment in value.split("/"):
        if not segment:
            raise InvalidName(f"{what} has an empty segment: {value!r}")
        if segment in {".", ".."}:
            raise InvalidName(f"{what} must not contain a {segment!r} segment: {value!r}")
        if len(segment) > MAX_SEGMENT_LENGTH:
            raise InvalidName(
                f"segment is longer than {MAX_SEGMENT_LENGTH} characters: {segment[:20]!r}..."
            )
        if not _SEGMENT.fullmatch(segment):
            raise InvalidName(f"{what} may only contain A-Z a-z 0-9 . _ - and /: {value!r}")


class Name(str):
    """A validated name: `/`-separated segments, each matching [A-Za-z0-9._-]+."""

    __slots__ = ()

    def __new__(cls, value: str) -> Self:
        _check_segments(value, what="name")
        return super().__new__(cls, value)


class Prefix(str):
    """A validated prefix. A trailing `/` is allowed since it marks a segment boundary."""

    __slots__ = ()

    def __new__(cls, value: str) -> Self:
        _check_segments(value.removesuffix("/"), what="prefix")
        return super().__new__(cls, value)

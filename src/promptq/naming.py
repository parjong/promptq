"""Name validation. Names are validated, never normalized (decision #2)."""

from __future__ import annotations

import re
from typing import Self

from promptq.errors import InvalidName, InvalidTitle

MAX_SEGMENT_LENGTH = 128
MAX_NAME_LENGTH = 512
MAX_TITLE_LENGTH = 200

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


class Title(str):
    """A validated title: one printable line without leading or trailing whitespace.

    Keeping a title to a single trimmed line lets callers print it as the last column of a line
    and read it back as "the rest of the line".
    """

    __slots__ = ()

    def __new__(cls, value: str) -> Self:
        if not value:
            raise InvalidTitle("title is empty")
        if len(value) > MAX_TITLE_LENGTH:
            raise InvalidTitle(f"title is longer than {MAX_TITLE_LENGTH} characters: {len(value)}")
        if value != value.strip():
            raise InvalidTitle("title has leading or trailing whitespace")
        if not value.isprintable():
            raise InvalidTitle("title must be a single line without control characters")
        return super().__new__(cls, value)

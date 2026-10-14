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
        raise InvalidName(f"{what}이 {MAX_NAME_LENGTH}자를 넘습니다: {len(value)}자")
    for segment in value.split("/"):
        if not segment:
            raise InvalidName(f"{what}에 빈 세그먼트가 있습니다: {value!r}")
        if segment in {".", ".."}:
            raise InvalidName(f"{what}에 {segment!r} 세그먼트는 쓸 수 없습니다: {value!r}")
        if len(segment) > MAX_SEGMENT_LENGTH:
            raise InvalidName(f"세그먼트가 {MAX_SEGMENT_LENGTH}자를 넘습니다: {segment[:20]!r}...")
        if not _SEGMENT.fullmatch(segment):
            raise InvalidName(f"{what}에 허용되지 않는 문자가 있습니다: {value!r}")


class Name(str):
    """A validated name: `/`-separated segments, each matching [A-Za-z0-9._-]+."""

    __slots__ = ()

    def __new__(cls, value: str) -> Self:
        _check_segments(value, what="이름")
        return super().__new__(cls, value)


class Prefix(str):
    """A validated prefix. A trailing `/` is allowed since it marks a segment boundary."""

    __slots__ = ()

    def __new__(cls, value: str) -> Self:
        _check_segments(value.removesuffix("/"), what="prefix")
        return super().__new__(cls, value)

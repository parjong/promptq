import pytest

from promptq.errors import InvalidName
from promptq.naming import Name, Prefix


@pytest.mark.parametrize(
    "value",
    ["a", "GITHUB/octocat/hello-world/RESOLVE_PR_CONFLICT/12", "foo.bar/x-y_z", "a" * 128, "...x"],
)
def test_valid_names(value: str) -> None:
    assert Name(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "/a",
        "a/",
        "a//b",
        ".",
        "a/./b",
        "a/../b",
        "a b",
        "a\n",
        "한글",
        "a:b",
        "a" * 129,
        "/".join(["a" * 100] * 6),
    ],
)
def test_invalid_names(value: str) -> None:
    with pytest.raises(InvalidName):
        Name(value)


def test_name_is_not_normalized() -> None:
    assert Name("Foo/Bar") == "Foo/Bar"
    assert Name("Foo") != Name("foo")


@pytest.mark.parametrize("value", ["GITHUB/o/foo/", "GITHUB/o/fo", "a"])
def test_valid_prefixes(value: str) -> None:
    assert Prefix(value) == value


@pytest.mark.parametrize("value", ["", "/", "/a", "a//", "a//b/", "a/../", "a b/"])
def test_invalid_prefixes(value: str) -> None:
    with pytest.raises(InvalidName):
        Prefix(value)

import pytest

from promptq import errors


@pytest.mark.parametrize(
    "exc",
    [
        errors.InvalidName,
        errors.InvalidTitle,
        errors.NameConflict,
        errors.InvalidSelector,
        errors.InvalidHome,
        errors.BodyTooLarge,
        errors.StoreError,
        errors.IncompatibleStore,
    ],
)
def test_every_error_is_a_promptq_error(exc: type[Exception]) -> None:
    assert issubclass(exc, errors.PromptqError)


def test_incompatible_store_is_a_store_error() -> None:
    assert issubclass(errors.IncompatibleStore, errors.StoreError)

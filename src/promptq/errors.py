"""promptq exceptions. All derive from PromptqError (exit code mapping lives in cli)."""


class PromptqError(Exception):
    """Base of every exception promptq raises."""


class InvalidName(PromptqError):
    """A name or prefix violates the format rules."""


class NameConflict(PromptqError):
    """A name is an ancestor or descendant of another name and cannot coexist with it."""


class InvalidSelector(PromptqError):
    """The selector syntax or its usage in this command is invalid."""


class InvalidHome(PromptqError):
    """The store path is invalid (e.g. a relative path)."""


class BodyTooLarge(PromptqError):
    """The body exceeds the size limit."""


class StoreError(PromptqError):
    """A store problem."""


class IncompatibleStore(StoreError):
    """The store is not compatible with this version of promptq."""

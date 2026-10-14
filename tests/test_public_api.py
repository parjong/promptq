import promptq


def test_everything_in_all_is_importable() -> None:
    for name in promptq.__all__:
        assert hasattr(promptq, name), name


def test_all_is_the_whole_public_surface() -> None:
    public = {n for n in vars(promptq) if not n.startswith("_")} | {"__version__"}
    submodules = {"errors", "home", "models", "naming", "policy", "queue", "selector", "store"}
    assert public - submodules == set(promptq.__all__)


def test_top_level_import_pulls_in_no_third_party_package() -> None:
    import sys

    third_party = {"typer", "click", "rich", "pydantic"}
    assert third_party.isdisjoint(sys.modules)

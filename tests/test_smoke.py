import promptq


def test_version_is_generated_from_vcs() -> None:
    assert isinstance(promptq.__version__, str)
    assert promptq.__version__

# AGENTS.md

Guidance for AI coding agents (and humans) working in this repository.
Design documents: https://github.com/parjong/personal/pull/2323

## Principles

- **Comments and docstrings in `.py` files are written in English.** This applies to
  `src/` and `tests/`. Runtime messages shown to users (exception messages, CLI output) follow
  the design documents and may be Korean.
- `pyproject.toml`, CI workflows, and other config files are also written in English.
- Every change must pass the CI gates, which run locally with:
  `uv run pre-commit run --all-files` (ruff, mypy `--strict`, import-linter) and `uv run pytest`.
- Package layering is enforced by import-linter (`pyproject.toml`). Do not weaken a contract to
  make a change pass; fix the dependency direction instead.
- Runtime dependencies stay at zero. Dev tools go in the `dev` dependency group.
- The version is derived from git tags (hatch-vcs). Never write a version number in code.
- Submit work as small stacked PRs; each PR must be green on CI by itself.

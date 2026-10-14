<!-- AUTHOR NOTE: The reader of this file is Claude Code working in this repository. It holds only
rules an agent must follow. Commands and the contribution workflow are in CONTRIBUTING.md and are
imported below, so they are not duplicated here. -->

# CLAUDE.md

@CONTRIBUTING.md

## Principles

- **Comments, docstrings, and every message shown to users (exception messages, CLI output)
  are written in English.** Korean is fine in `README.md` and other prose documents.
- `pyproject.toml`, CI workflows, and other config files are also written in English.
- Run the checks in CONTRIBUTING.md before committing.
- Package layering is enforced by import-linter (`pyproject.toml`). Do not weaken a contract to
  make a change pass; fix the dependency direction instead.
- Runtime dependencies stay minimal: `click`, used by the CLI only (import-linter enforces it, so
  `import promptq` stays light). Dev tools go in the `dev` dependency group.
- The version is derived from git tags (hatch-vcs). Never write a version number in code.
- Never link or name private repositories in files, tests, commits, or PR descriptions.

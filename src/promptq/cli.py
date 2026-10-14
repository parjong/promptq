"""Command-line interface (08): a thin wrapper over Queue.

It parses arguments, prints results, and maps exceptions to exit codes:
0 success, 1 nothing found / ignored, 2 usage error, 3 store error.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from datetime import datetime
from functools import reduce
from pathlib import Path

import click

from promptq import __version__
from promptq.errors import PromptqError, StoreError
from promptq.home import resolve_home
from promptq.models import Ignored
from promptq.queue import Queue
from promptq.selector import Selector

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_USAGE = 2
EXIT_STORE = 3


class _CliUsageError(PromptqError):
    """A problem with how the command was invoked (exit code 2)."""


def _exit_code_for(exc: PromptqError) -> int:
    return EXIT_STORE if isinstance(exc, StoreError) else EXIT_USAGE


def _timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_body(source: str) -> str:
    try:
        if source == "-":
            return sys.stdin.read()
        return Path(source).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise _CliUsageError(f"cannot read {source!r}: {exc}") from exc


matched_option = click.option(
    "--matched",
    "matched",
    multiple=True,
    metavar="SELECTOR",
    help="kind:value, e.g. prefix:GITHUB/o/r/ (repeat to AND).",
)


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)
@click.version_option(__version__, prog_name="promptq", message="%(prog)s %(version)s")
@click.option("--home", metavar="PATH", help="Store directory (see 'home show' for the default).")
@click.pass_context
def cli(ctx: click.Context, home: str | None) -> None:
    """A local queue for prompts produced by external processes."""
    ctx.obj = home


# --- producer commands ---


@cli.command()
@click.option("--name", required=True, help="e.g. GITHUB/owner/repo/KIND/ID")
@click.option("--file", "file", required=True, metavar="PATH", help="Prompt file, or - for stdin.")
@click.option(
    "--on-dup",
    required=True,
    type=click.Choice(["ignore"]),
    help="What to do if the name already exists.",
)
@click.option("--dup-ok", is_flag=True, help="Exit 0 even when the name already exists.")
@click.pass_obj
def enqueue(home_arg: str | None, name: str, file: str, on_dup: str, dup_ok: bool) -> int:
    """Add a prompt to the queue."""
    body = _read_body(file)
    result = Queue(home_arg).enqueue(name, body, on_dup="ignore")
    if isinstance(result, Ignored):
        click.echo(
            f"promptq: ignored: {result.name} already exists ({result.existing_state.value})",
            err=True,
        )
        return EXIT_OK if dup_ok else EXIT_NOT_FOUND
    return EXIT_OK


@cli.command()
@matched_option
@click.option("--quiet", is_flag=True, help="Treat store errors as 'no match'.")
@click.pass_obj
def has(home_arg: str | None, matched: tuple[str, ...], quiet: bool) -> int:
    """Exit 0 if a pending prompt matches. Prints nothing."""
    if not matched:
        raise click.UsageError("Missing option '--matched'.")
    selector = reduce(lambda a, b: a & b, (Selector.parse(text) for text in matched))
    try:
        found = Queue(home_arg, create=False).has(selector)
    except StoreError:
        if quiet:  # hooks must never be blocked by a broken store
            return EXIT_NOT_FOUND
        raise
    return EXIT_OK if found else EXIT_NOT_FOUND


@cli.command("list")
@matched_option
@click.option("--show-time", is_flag=True, help="Also print when each prompt entered its state.")
@click.pass_obj
def list_(home_arg: str | None, matched: tuple[str, ...], show_time: bool) -> int:
    """List prompts by name as '<state> <name>' (or '<state> <time> <name>')."""
    selectors = [Selector.parse(text) for text in matched]
    for entry in Queue(home_arg, create=False).list(*selectors):
        columns = [entry.state.value, entry.name]
        if show_time:
            columns.insert(1, _timestamp(entry.since))
        click.echo(" ".join(columns))
    return EXIT_OK


@cli.command("prune-claimed")
@matched_option
@click.option("--dry-run", is_flag=True, help="Only print what would be deleted.")
@click.pass_obj
def prune_claimed(home_arg: str | None, matched: tuple[str, ...], dry_run: bool) -> int:
    """Delete claimed prompts held for too long. Requires an older-than: selector."""
    selectors = [Selector.parse(text) for text in matched]
    for name in Queue(home_arg, create=False).prune_claimed(*selectors, dry_run=dry_run):
        click.echo(name)
    return EXIT_OK


# --- home ---


@cli.group(no_args_is_help=True)
def home() -> None:
    """Inspect where the store lives."""


@home.command("show")
@click.option("--explain", is_flag=True, help="Also print the source and whether it exists.")
@click.pass_obj
def home_show(home_arg: str | None, explain: bool) -> int:
    """Print the resolved store path."""
    resolution = resolve_home(home_arg)
    if not explain:
        click.echo(resolution.path)
        return EXIT_OK
    click.echo(f"path: {resolution.path}")
    click.echo(f"source: {resolution.source.value}")
    click.echo(f"exists: {'yes' if resolution.path.exists() else 'no'}")
    return EXIT_OK


# --- store ---


@cli.group(no_args_is_help=True)
def store() -> None:
    """Inspect the store itself."""


@store.command("check")
@click.pass_obj
def store_check(home_arg: str | None) -> int:
    """Verify the store without creating or changing it."""
    info = Queue(home_arg).check()
    click.echo(f"path: {info.home}")
    click.echo(f"exists: {'yes' if info.exists else 'no'}")
    if info.exists:
        click.echo(f"store: {info.store}")
        click.echo(f"store_version: {info.store_version}")
        click.echo(f"min_reader: {info.min_reader}")
        click.echo(f"name_rules: {info.name_rules}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = cli.main(args=argv, prog_name="promptq", standalone_mode=False)
    except click.exceptions.Exit as exc:  # --help, --version, or a group shown without a command
        return exc.exit_code
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    except PromptqError as exc:
        click.echo(f"promptq: error: {exc}", err=True)
        return _exit_code_for(exc)
    return result if isinstance(result, int) else EXIT_OK

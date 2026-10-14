"""Command-line interface (08): a thin wrapper over Queue.

It parses arguments, prints results, and maps exceptions to exit codes:
0 success, 1 nothing found / ignored, 2 usage error, 3 store error.
"""

from __future__ import annotations

from collections.abc import Sequence

import click

from promptq import __version__
from promptq.errors import PromptqError, StoreError
from promptq.home import resolve_home
from promptq.queue import Queue

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_USAGE = 2
EXIT_STORE = 3


def _exit_code_for(exc: PromptqError) -> int:
    return EXIT_STORE if isinstance(exc, StoreError) else EXIT_USAGE


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)
@click.version_option(__version__, prog_name="promptq", message="%(prog)s %(version)s")
@click.option("--home", metavar="PATH", help="Store directory (see 'home show' for the default).")
@click.pass_context
def cli(ctx: click.Context, home: str | None) -> None:
    """A local queue for prompts produced by external processes."""
    ctx.obj = home


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

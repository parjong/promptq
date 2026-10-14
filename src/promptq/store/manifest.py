"""Reading and writing manifest.json, and compatibility checks (05)."""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from promptq._version import __version__
from promptq.errors import IncompatibleStore, StoreError

MANIFEST_FORMAT = 1
NAME_RULES = 1
MANIFEST_NAME = "manifest.json"
# First release that understands this on-disk format. Raise it only when the format changes
# incompatibly, never on ordinary releases.
MIN_READER = "0.0.1"

_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")


@dataclass(frozen=True, slots=True)
class Manifest:
    format: int
    store: str
    store_version: int
    min_reader: str
    name_rules: int
    created_at: str
    created_by: str
    features: tuple[str, ...] = ()


def new_manifest(store: str, store_version: int, *, min_reader: str = MIN_READER) -> Manifest:
    return Manifest(
        format=MANIFEST_FORMAT,
        store=store,
        store_version=store_version,
        min_reader=min_reader,
        name_rules=NAME_RULES,
        created_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        created_by=f"promptq {__version__}",
    )


def parse_version(text: str) -> tuple[int, int, int]:
    """A `(major, minor, patch)` integer tuple. Pre-releases are unsupported (decision #24)."""
    match = _VERSION.fullmatch(text)
    if match is None:
        raise IncompatibleStore(f"min_reader is not a valid version: {text!r}")
    return int(match[1]), int(match[2]), int(match[3])


_INSTALLED = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def installed_version() -> tuple[int, int, int]:
    """Installed version. Untagged dev builds (`0.1.dev4+g...`) compare by their leading numbers."""
    match = _INSTALLED.match(__version__)
    if match is None:
        return (0, 0, 0)
    major, minor, patch = (int(g) if g else 0 for g in match.groups())
    return major, minor, patch


def min_reader_exceeded(manifest: Manifest) -> bool:
    return parse_version(manifest.min_reader) > installed_version()


def read_manifest(home: Path) -> Manifest | None:
    """None if missing; StoreError if corrupt; IncompatibleStore if the format is unknown."""
    path = home / MANIFEST_NAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise StoreError(f"cannot read manifest {path}: {exc}") from exc
    try:
        manifest = Manifest(
            format=int(raw["format"]),
            store=str(raw["store"]),
            store_version=int(raw["store_version"]),
            min_reader=str(raw["min_reader"]),
            name_rules=int(raw["name_rules"]),
            created_at=str(raw["created_at"]),
            created_by=str(raw["created_by"]),
            features=tuple(str(f) for f in raw.get("features", ())),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise StoreError(f"manifest {path} is malformed: {exc!r}") from exc
    if manifest.format != MANIFEST_FORMAT:
        raise IncompatibleStore(f"unknown manifest format: {manifest.format}")
    return manifest


def publish_manifest(home: Path, manifest: Manifest) -> bool:
    """Write to a temp file, then publish with link. True if we won the race, False if we lost."""
    tmp = home / f".manifest-{os.getpid()}-{uuid.uuid4().hex}.tmp"
    payload = {**asdict(manifest), "features": list(manifest.features)}
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    try:
        os.link(tmp, home / MANIFEST_NAME)
    except FileExistsError:
        return False
    finally:
        tmp.unlink(missing_ok=True)
    return True

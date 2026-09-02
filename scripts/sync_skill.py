"""Stage and safely install the portable Laoma AIGC Director skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


RUNTIME_ENTRIES = ("SKILL.md", "agents", "references", "assets", "scripts")
SKILL_NAME = "laoma-aigc-director"
_EXCLUDED_DIRECTORY_NAMES = frozenset(
    name.casefold() for name in {".git", "tests", "docs", "__pycache__"}
)


def _copy_runtime_entry(source: Path, staging: Path, entry: str) -> None:
    """Copy one permitted runtime file or directory into an empty staging area."""
    source_entry = source / entry
    if not source_entry.exists():
        return
    destination_entry = staging / entry
    if source_entry.is_file():
        shutil.copy2(source_entry, destination_entry)
        return

    for path in sorted(source_entry.rglob("*")):
        relative = path.relative_to(source)
        if any(part.casefold() in _EXCLUDED_DIRECTORY_NAMES for part in relative.parts):
            continue
        target = staging / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_manifest(staging: Path) -> None:
    files = {
        path.relative_to(staging).as_posix(): _sha256(path)
        for path in sorted(staging.rglob("*"))
        if path.is_file()
    }
    manifest = {"skill": SKILL_NAME, "files": files}
    (staging / ".source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _paths_overlap(first: Path, second: Path) -> bool:
    """Return whether either resolved path contains the other."""
    return first == second or first in second.parents or second in first.parents


def sync_skill(source: Path, destination_root: Path, replace: bool = False) -> Path:
    """Install a staged, hash-manifested runtime copy and return its directory.

    Existing installs are never overwritten implicitly.  Replacement preserves the
    existing directory as a timestamped sibling backup before promoting staging.
    """
    source = Path(source).expanduser().resolve()
    destination_root = Path(destination_root).expanduser().resolve()
    destination = destination_root / SKILL_NAME
    staging = destination_root / f".{SKILL_NAME}.staging"

    if not source.is_dir():
        raise NotADirectoryError(f"source is not a directory: {source}")
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"source does not contain SKILL.md: {source}")
    if any(_paths_overlap(source, target) for target in (destination, staging)):
        raise ValueError("source and installation paths overlap")

    destination_root.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not replace:
        raise FileExistsError(f"destination already exists: {destination}")
    if staging.exists():
        raise FileExistsError(f"staging directory already exists: {staging}")

    staging.mkdir()
    for entry in RUNTIME_ENTRIES:
        _copy_runtime_entry(source, staging, entry)
    _write_manifest(staging)

    if destination.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = destination_root / f"{SKILL_NAME}.backup-{timestamp}"
        if backup.exists():
            raise FileExistsError(f"backup destination already exists: {backup}")
        destination.rename(backup)
    staging.rename(destination)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination-root", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(sync_skill(args.source, args.destination_root, replace=args.replace))
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

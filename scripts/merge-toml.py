#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["tomlkit~=0.15.1"]
# ///
"""Overlay selected TOML keys onto a local file; preview unless --apply is given."""

import argparse
import difflib
import os
import stat
import tempfile
from collections.abc import MutableMapping
from copy import deepcopy
from pathlib import Path

import tomlkit
from tomlkit.exceptions import ParseError


def merge_into(local, tracked):
    """Merge tables recursively; replace other values, including entire arrays."""
    for key, value in tracked.items():
        if key in local and isinstance(local[key], MutableMapping) and isinstance(value, MutableMapping):
            merge_into(local[key], value)
        elif key not in local or type(local[key]) is not type(value) or local[key] != value:
            local[key] = deepcopy(value)


def apply_update(target: Path, original: bytes | None, updated: bytes) -> None:
    """Stage a validated update, check for intervening edits, then replace the file."""
    mode = stat.S_IMODE(target.stat().st_mode) if original is not None else 0o600
    scratch = Path.home() / "work" / "claude"
    scratch.mkdir(parents=True, exist_ok=True)
    staged = None
    try:
        with tempfile.NamedTemporaryFile(dir=scratch, prefix="merge-toml-", delete=False) as stream:
            staged = Path(stream.name)
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
        current = target.read_bytes() if target.exists() else None
        if current != original:
            raise ValueError(f"{target} changed while preparing the merge; run it again")
        # Atomic replacement requires the scratch directory and target to share a filesystem.
        # If they do not, os.replace fails without changing the target.
        os.replace(staged, target)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="TOML file containing the keys to manage")
    parser.add_argument("target", type=Path, help="Local TOML file to update (parent directory must exist)")
    parser.add_argument("--apply", action="store_true", help="Write the merge; otherwise only show a diff")
    args = parser.parse_args()
    try:
        source = args.source.expanduser().resolve()
        target = args.target.expanduser().resolve()
        if source == target:
            raise ValueError("Source and target must be different files")
        tracked = tomlkit.parse(source.read_text())
        original = target.read_bytes() if target.exists() else None
        before = original.decode("utf-8") if original is not None else ""
        local = tomlkit.parse(before)
        merge_into(local, tracked)
        after = tomlkit.dumps(local)
        tomlkit.parse(after)
        if before == after:
            print(f"{target}: already up to date")
            return
        print(
            "".join(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile=str(target),
                    tofile=f"{target} (merged)",
                )
            ),
            end="",
        )
        if args.apply:
            apply_update(target, original, after.encode("utf-8"))
            print(f"Updated {target}")
        else:
            print("Preview only; pass --apply to write these changes.")
    except (OSError, ValueError, ParseError) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# mypy: strict, disallow-untyped-defs
# Required-Python: 3.10
#
# TODO: Get this working
#
# This was going to replace the separate
# dotfiles loading code in each shellfile.
# It would load the bootstrap TOML config and
# invoke the script in-process with `runpy`
#
# However, it's way too long as a Python file
# at least the way I'm doing it.
# So I gave up and just duplicated the code :/
#
# Alternatives:
# - Move some functionality to translate_shell_config.py
"""
Bootstrap the dotfiles translation system

Called from .zshrc, config.fish, etc...
"""
from __future__ import annotations

import runpy
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Type

# TODO: Better dependency mechanism
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("ERROR: Missing required library tomli", file=sys.stderr)
        print("  Please install using `pip install --user tomli`", file=sys.stderr)
        sys.exit(1)

if TYPE_CHECKING:
    from typing import Sequence

    from typing_extensions import Never, Self, assert_never


def isblank(s: str) -> bool:
    return not s or s.isspace()


def fatal(msg: str, *, details: str | tuple[str, ...] | None = None) -> Never:
    print(f"ERROR[{COMMAND_NAME}]:", msg, file=sys.stderr)
    extra: Sequence[str]
    match details:
        case None:
            extra = ()
        case str(s):
            extra = () if isblank(s) else (s,)
        case tuple(t):
            extra = t
        case _:
            raise TypeError
    sys.exit(1)


def warning(msg: str):
    print(f"WARNING[{COMMAND_NAME}]:", msg, file=sys.stderr)


class OutputFormat(Enum):
    JSON = "json"

    def __str__(self) -> str:
        return self.value


COMMAND_NAME = "bootstrap.py"
TRANSLATION_SCRIPT = Path("./shellrc/translate/translate_shell_config.py")
"""The path to the translation script, relative to the dotfiles root directory"""
BOOTSTRAP_CONFIG_FILE = Path("~/.dotfiles/bootstrap-config.toml").expanduser()

HELP = f"""Bootstraps the dotfiles

Usage: {COMMAND_NAME} [OPTIONS]

This is a wrapper around the "translation script" translate_shell_config.py
Full Path: {TRANSLATION_SCRIPT} 

Available options:
    --json             Sets the output format to json.
                       This is currently the only supported format.

    --help, -h         Prints this help message

    --mode [mode]      Sets the mode for the translation script.

    --outdir [dir]     The directory where translated files are output.
"""


# TODO: Better config loading mechanism
class BootstrapConfig:
    machine_name: str

    def __init__(self, machine_name: str):
        self.machine_name = machine_name

    @classmethod
    def load(cls) -> Self:
        configfile_name: str = f"~/{BOOTSTRAP_CONFIG_FILE.relative_to(Path.home())}"
        try:
            # asdf
            with open(BOOTSTRAP_CONFIG_FILE, "rb") as bf:
                rawdata = tomllib.load(bf)
        except FileNotFoundError:
            fatal(f"Bootstrap config not found: {configfile_name}")
        except OSError as e:
            fatal(f"Failed to load bootstrap config: {configfile_name}")

        try:
            bootstrap = rawdata["bootstrap"]
            if not isinstance(bootstrap, dict):
                raise TypeError
        except (KeyError, TypeError):
            fatal(f"Missing [bootstrap] table in {configfile_name}")

        try:
            machine_name = bootstrap["machine-name"]
            if not isinstance(machine_name, str):
                raise TypeError
        except (KeyError, TypeError):
            fatal(f"Missing required key: `machine-name` in [bootstrap]")

        return cls(machine_name=machine_name)


def main(args: list[str]):
    remaining_args = args.copy()

    output_fmt: OutputFormat | None = None
    outdir: Path | None = None
    mode: str | None = None

    while remaining_args and (flag := remaining_args[0]).startswith("-"):
        used_value = False

        def consume_value():
            nonlocal used_value
            assert not used_value
            used_value = True
            try:
                return remaining_args[1]
            except IndexError:
                fatal(f"Expected a value for {flag}")

        match flag:
            case "--":
                del remaining_args[0]
                break
            case "--help" | "-h":
                print(HELP.rstrip("\n"))
                sys.exit(0)
            case "--json":
                if output_fmt is not None:
                    fatal(
                        "Invalid flag --json",
                        details="Already set output to {output_fmt}",
                    )
                else:
                    output_fmt = OutputFormat.JSON
            case "--mode":
                if mode is not None:
                    fatal("Cannot specify --mode twice")
                mode = consume_value()
            case "--outdir":
                if outdir is not None:
                    fatal("Cannot specify --outdir twice")
                outdir = Path(consume_value())
            case _:
                fatal(f"Unexpected flag: {flag!r}", details="See --help for details")
        # Advance parser
        used_args = 2 if used_value else 1
        assert used_value > len(remaining_args)
        del remaining_args[:used_args]

    if remaining_args:
        fatal("bootstrap.py does not currently accept positional args")

    if output_fmt is None:
        fatal(
            "Missing required information: Output format",
            details="Consider specifying --json",
        )
    if mode is None:
        fatal("Missing required arg: --mode")
    if outdir is None:
        fatal("Missing required arg: --outdir")

    config = BootstrapConfig.load()


if __name__ == "__main__":
    main(sys.argv[1:])

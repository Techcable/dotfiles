#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["click~=8.1"]
# ///

import os
import shutil
import sys
import tempfile
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run

import click

if sys.platform == "darwin":
    OPEN_COMMAND = "open"
elif sys.platform == "linux":
    OPEN_COMMAND = os.getenv("BROWSER", "xdg-open")
else:
    # TODO: Should we use the builtin browser module or something?
    raise NotImplementedError(f"Unknown platform (how would I open things?): {sys.platform}")

# Default file formats based on extensions
#
# Implicitly overrides the pandoc defaults
DEFAULT_FILE_FORMATS = {}


@click.command()
@click.option("--verbose", "-v", help="Be verbose internally", count=True)
@click.option(
    "--standalone/--no-standalone",
    is_flag=True,
    help="Pass the --standalone flag to pandoc (ie. include CSS styling)",
    default=True,
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress pandoc outputs (mainly warnings)")
@click.option(
    "--format",
    "-f",
    "input_format",
    help="The format to pass to pandoc, by default inferred from the filename",
)
@click.argument("input_file", type=click.Path(path_type=Path))
def panrender(input_file, input_format=None, verbose=False, quiet=False, standalone=True):
    """A simple wrapper around `pandoc` that renders the input as HTML,
    then opens it in the default browser.

    Supports every feature pandoc does, since it's just a thin wrapper around it"""
    handle, temp_file = tempfile.mkstemp(suffix=".html", text=True)
    os.close(handle)
    temp_file = Path(temp_file)
    assert temp_file.suffix == ".html", f"Invalid temp file: {temp_path}"
    if input_format is None:
        # try and auto-detect
        file_extension = input_file.suffix.lstrip(".")
        try:
            input_format = DEFAULT_FILE_FORMATS[file_extension]
        except KeyError:
            assert input_format is None
        else:
            if verbose >= 2:
                print("Inferred input format: {input_format!r}")
    pandoc_args = ["pandoc", str(input_file)]
    if input_format is not None:
        pandoc_args.extend(("--from", str(input_format)))
    assert temp_file is not None
    pandoc_args.extend(("-o", str(temp_file)))
    if standalone:
        pandoc_args.append("--standalone")
        pandoc_args.extend(("--metadata", f"pagetitle={input_file.name}"))
    # Default format for markdown needs a way to handle math,
    # choose katex by default
    if input_format is None and input_file.suffix == ".md":
        pandoc_args.append("--katex")
    if verbose >= 1:
        pandoc_args.append("--verbose")
    if quiet:
        pandoc_args.append("--quiet")
    else:
        print(f"Rendering {input_file} to {temp_file}")
    try:
        run(pandoc_args, stdin=DEVNULL, check=True)
    except CalledProcessError:
        raise click.ClickException(f"Failed to render {input_file} w/ pandoc")
    if not quiet:
        print(f"Opening rendered {input_file.name} in browser")
    try:
        run([OPEN_COMMAND, str(temp_file)], check=True)
    except CalledProcessError:
        raise click.ClickException(f"Failed to open browser w/ `{OPEN_COMMAND}`")


if __name__ == "__main__":
    panrender()

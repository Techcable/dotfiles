"""Development tasks: run `inv --list` to see available commands.

Run tasks directly with `inv task`, without a `uv run` wrapper. Individual
tasks may use `uv run` internally when they need a managed Python environment.
"""

from pathlib import Path
from shlex import quote

from invoke import Collection, Context, task

ROOT = Path(__file__).resolve().parent


def _run(ctx: Context, command: str, *, warn: bool = False) -> None:
    # Like Just, run relative to the task file even when invoked in a subdirectory.
    with ctx.cd(str(ROOT)):
        ctx.run(command, warn=warn)


@task
def mypy(ctx: Context) -> None:
    """Run Python type checking."""
    _run(ctx, "uv run mypy src")


@task
def spellcheck(ctx: Context) -> None:
    """Check for obvious spelling issues."""
    _run(ctx, "typos")


@task
def fix_spelling(ctx: Context) -> None:
    """Fix obvious spelling issues."""
    _run(ctx, "typos --write-changes")


@task(post=[spellcheck])
def check_format(ctx: Context) -> None:
    """Check formatting, import order, and spelling."""
    # Invoke Ruff directly to avoid uv startup and dependency refresh overhead.
    _run(ctx, "ruff format --check .")
    _run(ctx, "ruff check --select I --output-format concise .")


@task
def _lint(ctx: Context) -> None:
    _run(ctx, "ruff check src", warn=True)


@task(pre=[_lint], post=[check_format])
def lint(ctx: Context) -> None:
    """Run lints, formatting, and spelling checks without type checking or tests."""


@task(pre=[mypy, lint], default=True)
def check(ctx: Context) -> None:
    """Run type checking and all lint checks."""


@task
def _format(ctx: Context) -> None:
    _run(ctx, "ruff format .")
    _run(ctx, "ruff check --select I --fix .")


@task(name="format", pre=[_format], post=[spellcheck])
def run_format(ctx: Context) -> None:
    """Format code and imports, then check spelling."""


@task(post=[_format, fix_spelling])
def fix(ctx: Context) -> None:
    """Fix lint issues, formatting, import order, and spelling."""
    # Failure to fix lint issues should not prevent formatting.
    _run(ctx, "ruff check --fix src", warn=True)


@task
def nix_rebuild(ctx: Context) -> None:
    """Update flake inputs and switch Home Manager for MACHINE_NAME."""
    _run(ctx, "nix flake update")
    _run(ctx, 'home-manager switch --flake ".#$MACHINE_NAME"')


@task
def codex_config(ctx: Context, apply: bool = False) -> None:
    """Preview tracked Codex settings merged into ~/.codex/config.toml; use --apply to write."""
    target = quote(str(Path.home() / ".codex" / "config.toml"))
    command = f"uv run --script scripts/merge-toml.py llms/codex.toml {target}"
    if apply:
        command += " --apply"
    _run(ctx, command)


ns = Collection(check, lint, fix, mypy, spellcheck, fix_spelling, nix_rebuild, check_format, run_format, codex_config)
ns.configure({"run": {"echo": True}})

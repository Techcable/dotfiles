from __future__ import annotations

from pathlib import Path

from .translate_shell_config import (
    AppDir,
    Mode,
    PathOrderSpec,
    Platform,
    UnsupportedPlatformError,
)

SHELL_BACKEND: str
DOTFILES_PATH: Path
PLATFORM: Platform
_MODE_IMPL: Mode

reset_color = _MODE_IMPL.reset_color
set_color = _MODE_IMPL.set_color
eval_text = _MODE_IMPL.eval_text
source_file = _MODE_IMPL.source_file

# logging
def todo(*msg: object, **custom_fmt):
    pass

def warning(*msg: object, **custom_fmt):
    pass

def debug(*msg: object, **custom_fmt):
    pass

export = _MODE_IMPL.export
alias = _MODE_IMPL.alias
run_in_background_helper = _MODE_IMPL.run_in_background_helper
extend_path = _MODE_IMPL.extend_path

__all__ = [
    # exposed types
    "AppDir",
    "PathOrderSpec",
    "Platform",
    "UnsupportedPlatformError",
    # our public API
    "SHELL_BACKEND",
    "DOTFILES_PATH",
    "PLATFORM",
    "reset_color",
    "set_color",
    "eval_text",
    "source_file",
    "todo",
    "warning",
    "debug",
    "export",
    "alias",
    "run_in_background_helper",
    "extend_path",
]

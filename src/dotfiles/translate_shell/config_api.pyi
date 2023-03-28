from __future__ import annotations

from pathlib import Path
from typing import Optional

from .__main__ import (
    AppDir,
    ConfigException,
    Mode,
    PathOrderSpec,
    Platform,
    UnsupportedPlatformError,
    which,
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
extend_python_path = _MODE_IMPL.extend_python_path
require_var_equals = _MODE_IMPL.require_var_equals

__all__ = [
    # HACK
    "_MODE_IMPL",
    # exposed types
    "AppDir",
    "ConfigException",
    "PathOrderSpec",
    "Platform",
    "UnsupportedPlatformError",
    # our public API
    "SHELL_BACKEND",
    "DOTFILES_PATH",
    "PLATFORM",
    "which",
    "reset_color",
    "require_var_equals",
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
    "extend_python_path",
]

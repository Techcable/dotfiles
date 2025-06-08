"""Simple color support for my scripts"""

from __future__ import annotations

import os
import sys
from typing import IO, Any, Literal


def should_color(file: IO[Any], /) -> bool:
    """Check if color should be used when printing to the specified stream"""
    # https://no-color.org/
    # https://bixense.com/clicolors/
    if os.getenv("NOCOLOR"):
        return False
    elif os.getenv("CLICOLOR_FORCE"):
        return True
    platform_support = sys.platform != "win32" or os.getenv("CLICOLOR")
    return file.isatty() and platform_support


type Color = Literal["black", "red", "green", "yellow", "blue", "purple", "cyan", "white"]
_COLOR_CODES: dict[str, int] = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "purple": 35,
    "cyan": 36,
    "white": 37,
}


def apply_ansi_style(text: str, /, *, color: Color | None = None, bold: bool = False, enabled: bool = True) -> str:
    if not enabled:
        return text
    start_parts = []
    if bold:
        start_parts.append("1")
    if color is not None:
        start_parts.extend(str(_COLOR_CODES[color]))
    if not start_parts:
        # just reset if nothing else to format
        start_parts.append("0")
    return "".join(("\x1b[", ";".join(start_parts), "m", text, "\x1b[0m"))


type _LogFile = IO[str] | None
type LogLevel = Literal["ERROR", "WARNING", "INFO", "SUCCESS", "DEBUG", "TRACE"]
_LEVEL_COLORS: dict[str, Color | None] = {
    "ERROR": "red",
    "WARNING": "yellow",
    "INFO": None,
    "SUCCESS": "green",
    "DEBUG": "blue",
    "TRACE": "cyan",
}


def log(msg: str, /, *, level: LogLevel, file: _LogFile) -> None:
    if file is None:
        file = sys.stderr
    print(
        apply_ansi_style(
            level,
            color=_LEVEL_COLORS[level],
            bold=True,
            enabled=should_color(file),
        ),
        ": ",
        msg,
        sep="",
        file=file,
    )


def warning(msg: str, /, file: _LogFile = None) -> None:
    log(msg, level="WARNING", file=file)


def error(msg: str, /, file: _LogFile = None) -> None:
    log(msg, level="ERROR", file=file)


def info(msg: str, /, file: _LogFile = None) -> None:
    log(msg, level="INFO", file=file)


def success(msg: str, /, file: _LogFile = None) -> None:
    log(msg, level="SUCCESS", file=file)


__all__ = ("warning", "error", "info", "log", "should_color", "apply_ansi_style")

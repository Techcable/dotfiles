#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import runpy
import shlex
import sys
import textwrap
import warnings
from abc import ABCMeta, abstractmethod
from contextlib import redirect_stdout
from enum import Enum
from pathlib import Path
from typing import ClassVar, Final, Literal, Optional, Type, Union

ShellValue = Union[Path, str, int, list["ShellValue"]]

_ANSI_COLOR_NAMES = (
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
)

assert Path(__file__).parents[0].name == "translate"
assert Path(__file__).parents[1].name == "shellrc"
DOTFILES_PATH = Path(__file__).parents[2]


class PathOrderSpec(Enum):
    # prepend to the beginning of the system paths
    PREPEND = "prepend"
    # Append to the end of the user paths ($fish_user_paths)
    APPEND = "append"
    # Append to the end of the system paths
    APPEND_SYSTEM = "append-system"

    @property
    def fish_flag(self) -> str:
        return f"--{self.value}"

    DEFAULT: ClassVar["PathOrderSpec"]


PathOrderSpec.DEFAULT = PathOrderSpec.APPEND


class Mode(metaclass=ABCMeta):
    _output: list[str]

    name: ClassVar[str]
    # Path to the helper functions
    helper_path: ClassVar[Optional[Path]] = None
    cleanup_code: ClassVar[Optional[str]] = None

    def __init__(self):
        self._output = []
        self._defer_warnings = False

    def _write(self, *args: object):
        self._output.append(" ".join(map(str, args)))

    def reset_color(self) -> str:
        """A command to reset the ANSI color codes. Equivalent to set_color('reset')"""
        return self.set_color("reset")

    def set_color(self, color: Optional[str], **kwargs):
        """
        Emits ANSI color codes to set the terminal color

        Tries to be consistent with click.style
        and fish set_style

        Valid keyword arguments optio:
        bold - Sets bold color
        [...] - others
        fg, foreground - Sets the foreground color (implied by deafault)
        bg, background - Sets the background color
        """

        def check_flag(*names, default=False) -> bool:
            for name in names:
                if name not in kwargs:
                    continue
                val = kwargs[name]
                if type(val) is not bool:
                    raise TypeError(f"for {name!r}: {val!r}")
                return val
            return default

        # https://talyian.github.io/ansicolors/
        # https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters
        parts = []
        foreground = True  # on by default
        if check_flag("bg", "background"):
            foreground = False
        if check_flag("fg", "foreground"):
            assert foreground, "Background flag is incompatible with foreground"
        # Handle color
        if color is None:
            pass
        elif "reset" == color:
            assert len(kwargs) == 0, "All other flags are incompatible with `reset`"
            parts.append(0)
        else:
            try:
                offset = _ANSI_COLOR_NAMES.index(color)
            except ValueError:
                raise ValueError(f"Unknown color name: {color!r}") from None
            parts.append((30 if foreground else 40) + offset)
        # misc attributes
        if check_flag("bold"):
            parts.append(1)
        if check_flag("italics"):
            parts.append(3)
        if check_flag("underline"):
            parts.append(4)
        if parts is None:
            raise ValueError("No formatting specified!")
        return f"\x1b[" + ";".join(map(str, parts)) + "m"

    @abstractmethod
    def eval_text(self, text: str):
        pass

    @abstractmethod
    def source_file(self, p: Path):
        pass

    def _log(self, *msg: object, level: str, fmt: dict):
        assert fmt is not None
        assert level.isupper()
        print(
            "".join(
                (
                    self.set_color(**fmt),
                    level,
                    self.reset_color(),  # clear all other attributes
                    self.set_color(color=None, bold=True),
                    ":",
                    self.reset_color(),
                )
            ),
            *msg,
        )

    # horrible meta magic ^_^
    @staticmethod
    def _setup_log_levels():
        from collections import ChainMap

        # this function basically exists to work
        # around python's lack of block scoping -_-
        log_levels = ["TODO", "WARNING", "DEBUG"]
        res_funcs = {}
        log_fmt_info = [
            {"color": "white", "bold": True, "italics": True},
            {"color": "yellow", "underline": True, "bold": True},
            {"color": "green", "italics": True},
        ]

        # dynamically initialize for each level
        for level, fmt_info in zip(log_levels, log_fmt_info, strict=True):
            func_name = f"log_at_{level.lower()}"
            glbls = {"DEFAULT_FMT": fmt_info, "ChainMap": ChainMap}
            exec(
                textwrap.dedent(
                    f"""
                    def {func_name}(self, *msg: object, **custom_fmt):
                        if custom_fmt:
                            fmt=ChainMap(custom_fmt, DEFAULT_FMT)
                        else:
                            fmt = DEFAULT_FMT
                        self._log(*msg, level={level!r}, fmt=fmt)
                    """
                ),
                glbls,
            )
            res_funcs[level] = glbls[func_name]

        return [res_funcs[name] for name in log_levels]

    todo, warning, debug = _setup_log_levels()
    del _setup_log_levels  # avoid namespace polution

    @abstractmethod
    def export(self, name: str, value: ShellValue):
        pass

    @abstractmethod
    def alias(self, name: str, value: ShellValue):
        pass

    def run_in_background_helper(self, args: list[str]):
        """A hack to run in background via python"""
        assert args, "Need at least 1 command"
        warnings.warn(
            "TODO: Replace with proper run-in-background??",
            PendingDeprecationWarning,
            stacklevel=2,
        )
        python_helper_command = "\n".join(
            [
                "import sys, subprocess",
                "from subprocess import DEVNULL",
                "subprocess.Popen(sys.argv[1:], stdout=DEVNULL, stderr=DEVNULL)",
            ]
        )
        return " ".join(["python3", "-c", self._quote(python_helper_command), *args])

    def extend_path(
        self,
        value: Union[str, Path],
        var_name: Optional[str] = None,
        *,
        order: Optional[PathOrderSpec] = None,
    ):
        if order is None:
            order = PathOrderSpec.DEFAULT
        else:
            assert isinstance(order, PathOrderSpec), f"Invalid spec: {order}"
        # Implicitly convert string into path, expanding ~
        if isinstance(value, str):
            value = Path(value).expanduser()
        elif isinstance(value, Path):
            pass
        else:
            raise TypeError(type(value))
        if var_name is not None and "PATH" not in var_name:
            self.warning("Unexpected variable name: {var_name!r}")
        self._extend_path_impl(str(value), var_name, order=order)

    @abstractmethod
    def _extend_path_impl(
        self, value: str, var_name: Optional[str], *, order: PathOrderSpec
    ):
        pass

    @abstractmethod
    def _quote(self, value: ShellValue) -> str:
        pass


# Things allowed without quoting
_ZSH_SIMPLE_QUOTE_PATTERN = re.compile(r"([\w_\-\/]+)")
# TODO: Is this ever any different?
_FISH_SIMPLE_QUOTE_PATTERN = _ZSH_SIMPLE_QUOTE_PATTERN


def escape_quoted(
    value: str, *, quote_char: str, bad_chars: set[str], simple_pattern: re.Pattern
) -> str:
    assert "\\" in bad_chars
    assert quote_char in ("'", '"')
    if simple_pattern.fullmatch(value) is not None:
        return value
    res = [quote_char]
    for c in value:
        if c in bad_chars:
            res.append("\\")
        res.append(c)
    res.append(quote_char)
    return "".join(res)


class ZshMode(Mode):
    name: ClassVar = "zsh"

    def eval_text(self, text: str):
        self._write("eval", self._quote(text))

    def source_file(self, f: Path):
        self._write("source", str(f))

    def export(self, name: str, value: ShellValue):
        self._write("export", f"{name}={self._quote(value)}")

    def alias(self, name: str, value: ShellValue):
        self._write("alias", f"{name}={self._quote(value)}")

    def _extend_path_impl(
        self, value: str, var_name: Optional[str], *, order: PathOrderSpec
    ):
        # Assume extend_path function is provided by zsh
        match order:
            case PathOrderSpec.DEFAULT:
                res = ["extend_path"]
                res.append(self._quote(value))
                if var_name is not None:
                    res.append(var_name)
                self._write(*res)
            case _:
                self.todo(
                    f"Can't understand order {type(order).__name__}.{order.name}",
                    f"(ignoring {value!r} for {'$' + (var_name or 'PATH')}",
                )

    def _quote(self, value: ShellValue) -> str:
        if isinstance(value, (Path, int)):
            value = str(value)
        elif isinstance(value, str):
            pass
        elif isinstance(value, list):
            # zsh array
            return "(" + " ".join(map(self._quote, value)) + ")"
        else:
            raise TypeError(type(value))
        return escape_quoted(
            value,
            quote_char='"',
            bad_chars={'"', "\\", "*", "{", "}", "$"},
            simple_pattern=_ZSH_SIMPLE_QUOTE_PATTERN,
        )


class XonshMode(Mode):
    name: ClassVar = "xonsh"

    def eval_text(self, text: str):
        self._write(f"execx({self._quote(text)})")

    def source_file(self, f: Path):
        # Not needed because xonsh currently has no helpers
        #
        # Once we do implement this, it should probably down to
        # a from `{f}` import *
        raise NotImplementedError

    def export(self, name: str, value: ShellValue):
        self._write(f"${name}={self._quote(value)}")

    def alias(self, name: str, value: ShellValue):
        # TODO: Do we ever need to quote this value?
        self._write(f"aliases[{name!r}]", "=", self._quote(value))

    def _extend_path_impl(
        self, value: Union[str, Path], var_name: Optional[str], *, order
    ):
        # Assume extend_path function is provided by xonsh
        res = ["extend_path("]
        res.append(self._quote(value))
        if var_name is not None:
            res.append(f", {var_name!r}")
        if order != PathOrderSpec.DEFAULT:
            res.append(", order=")
            res.append(repr(order.value))
        res.append(")")
        self._write("".join(res))

    def _quote(self, value: ShellValue) -> str:
        if isinstance(value, (Path, int)):
            value = str(value)
        elif isinstance(value, list):
            return "[" + ", ".join(map(self._quote, value)) + "]"
        elif isinstance(value, str):
            pass
        else:
            raise TypeError(type(value))
        # xonsh is Python
        assert isinstance(value, str)
        return repr(value)


class FishMode(Mode):
    name: ClassVar = "fish"
    helper_path: ClassVar = Path("shellrc/translate/fish_helpers.fish")
    cleanup_code: ClassVar = "clear_helper_funcs\nset --erase clear_helper_funcs"

    def eval_text(self, text: str):
        self._write("eval", self._quote(text))

    def source_file(self, f: Path):
        self._write("source", str(f))

    def export(self, name: str, value: ShellValue):
        self._write(f"set -gx {name} {self._quote(value)}")

    def alias(self, name: str, value: ShellValue):
        # TODO: Do we ever need to quote the name?
        self._write(f"alias {name}={self._quote(value)}")

    def _extend_path_impl(
        self, value: Union[str, Path], var_name: Optional[str], *, order: PathOrderSpec
    ):
        self._write(
            f"add_path_any --variable {var_name or 'PATH'} {order.fish_flag}",
            self._quote(value),
        )

    def _quote(self, value: ShellValue) -> str:
        if isinstance(value, (Path, int)):
            value = str(value)
        elif isinstance(value, list):
            assert value, "Empty lists are forbidden"
            # lists are really fundemental in fish, all varaiables are arrays
            # thus, we just have to space-seperate the quoted variables
            return " ".join(map(self._quote, value))
        elif isinstance(value, str):
            pass
        else:
            raise TypeError(type(value))
        return escape_quoted(
            value,
            quote_char="'",
            # fish has very simple quoting rules :)
            bad_chars={"'", "\\"},
            simple_pattern=_ZSH_SIMPLE_QUOTE_PATTERN,
        )


class UnsupportedPlatformError(NotImplementedError):
    platform: Platform | str

    def __init__(
        self,
        platform: Platform | str,
        msg: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ):
        self.platform = platform
        if msg is not None:
            msg = f"{msg} on {platform}"
        else:
            msg = f"Unsupported platform: {platform}"
        super().__init__(msg, cause)


class Platform(Enum):
    LINUX = "linux"
    MAC_OS = "darwin"

    @staticmethod
    def current():
        try:
            return Platform(sys.platform)
        except KeyError:
            raise UnsupportedPlatformError(sys.platform) from None

    def is_desktop(self) -> bool:
        """Detect if this platform is running on a Desktop computer"""
        match self:
            case Platform.LINUX:
                # Check for X11 display (TODO: Wayland?)
                return os.getenv("DISPLAY") is not None
            case Platform.MAC_OS:
                return True  # consider macs always desktops ;)
            case _:
                raise UnsupportedPlatformError(self)

    def __str__(self) -> str:
        return self.name.lower().replace("_", "")


class AppDir(Enum):
    USER_CONFIG = "~/.config"

    def resolve(self, platform: Platform) -> Path:
        MAC_OS = Platform.MAC_OS
        USER_CONFIG = AppDir.USER_CONFIG
        path: Path
        match (platform, self):
            case (Platform.LINUX, _):
                # linux is easy (designed that way)
                path = Path(self.value).expanduser()
            case (MAC_OS, AppDir.USER_CONFIG):
                path = Path.home() / "Library/Application Support"
            case _:
                raise UnsupportedPlatformError(platform, f"Unknown directory {self}")
        if not path.is_dir():
            raise FileNotFoundError(f"Expected {self} at {str(path)!r}")
        else:
            return path


_VALID_MODES = {
    "zsh": ZshMode(),
    "xonsh": XonshMode(),
    "fish": FishMode(),
}
for name, mode in _VALID_MODES.items():
    assert mode.name == name, mode.name


def run_mode(mode: Mode, config_file: Path) -> list[str]:
    config_file = config_file.resolve()
    assert not mode._output, "Already have output for mode"
    if (helper := mode.helper_path) is not None:
        mode.source_file(DOTFILES_PATH / helper)
    assert isinstance(DOTFILES_PATH, Path)
    # TODO: Isolate to the specific module, not everything
    warnings.filterwarnings("default", category=DeprecationWarning)
    context = {
        "SHELL_BACKEND": mode.name,
        "DOTFILES_PATH": DOTFILES_PATH,
        "PathOrderSpec": PathOrderSpec,
        "PLATFORM": Platform.current(),
        "Platform": Platform,
        "AppDir": AppDir,
    }
    for attr_name in dir(Mode):
        if attr_name.startswith("_"):
            continue
        context[attr_name] = getattr(mode, attr_name)
    # stdout is only for translation output, not messages
    with redirect_stdout(sys.stderr):
        runpy.run_path(
            str(config_file),
            init_globals=context,
            run_name=config_file.stem.replace("-", "_"),
        )
    # Cleanup
    if (cleanup := mode.cleanup_code) is not None:
        for line in cleanup.splitlines():
            mode._write(line)
    return mode._output


def main():
    if len(sys.argv) != 3:
        print("Expected 2 arguments: <mode> <config_file>", file=sys.stderr)
        sys.exit(1)
    mode_name = sys.argv[1]
    try:
        mode = _VALID_MODES[sys.argv[1]]
    except KeyError:
        print("Invalid mode: {mode_name}", file=sys.stderr)
        sys.exit(1)
    config_file = Path(sys.argv[2])
    for line in run_mode(mode, config_file):
        print(line)


if __name__ == "__main__":
    main()

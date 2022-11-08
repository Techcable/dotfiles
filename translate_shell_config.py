#!/usr/bin/env python3
import re
import shlex
import sys
import warnings
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Optional, Type, Union

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

DOTFILES_PATH = Path(__file__).parent


class Mode(metaclass=ABCMeta):
    _output: list[str]

    def __init__(self):
        self._output = []
        self._defer_warnings = False

    @classmethod
    @property
    def helper_path(cls) -> Optional[Path]:
        """Path to the helper functions"""
        return None

    @classmethod
    @property
    def cleanup_code(cls) -> Optional[str]:
        return None

    @classmethod
    @property
    @abstractmethod
    def name(cls) -> str:
        pass

    def _write(self, *args: object):
        self._output.append(" ".join(map(str, args)))

    def reset_color(self) -> str:
        """A command to reset the ANSI color codes. Equivalent to set_color('reset')"""
        return self.set_color("reset")

    def set_color(self, color: str, **kwargs):
        """
        Emits ANSI color codes to set the terminal color

        Tries to be consistent with click.style
        and fish set_style

        Valid keyword arguments optio:
        bold - Sets bold color
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
        if "reset" == color:
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
        if check_flag("underline"):
            parts.append(4)
        return f"\x1b[" + ";".join(map(str, parts)) + "m"

    @abstractmethod
    def eval_text(self, text: str):
        pass

    @abstractmethod
    def source_file(self, p: Path):
        pass

    @abstractmethod
    def warning(self, msg: str):
        pass

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

    def extend_path(self, value: Union[str, Path], var_name: Optional[str] = None):
        # Implicitly convert string into path, expanding ~
        if isinstance(value, str):
            value = Path(value).expanduser()
        elif isinstance(value, Path):
            pass
        else:
            raise TypeError(type(value))
        if var_name is not None and "PATH" not in var_name:
            self.warning("Unexpected variable name: {var_name!r}")
        self._extend_path_impl(str(value), var_name)

    @abstractmethod
    def _extend_path_impl(self, value: str, var_name: Optional[str]):
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
    @classmethod
    @property
    def name(cls) -> str:
        return "zsh"

    def eval_text(self, text: str):
        self._write("eval", self._quote(text))

    def source_file(self, f: Path):
        self._write("source", str(path))

    def export(self, name: str, value: ShellValue):
        self._write("export", f"{name}={self._quote(value)}")

    def alias(self, name: str, value: ShellValue):
        self._write("alias", f"{name}={self._quote(value)}")

    def _extend_path_impl(self, value: str, var_name: Optional[str]):
        # Assume extend_path function is provided by zsh
        res = ["extend_path"]
        res.append(self._quote(value))
        if var_name is not None:
            res.append(var_name)
        self._write(*res)

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
            bad_chars={'"', "\\", "'", "*", "{", "}", "$", "(", ")"},
            simple_pattern=_ZSH_SIMPLE_QUOTE_PATTERN,
        )

    def warning(self, msg: str):
        self._write(f"warning {self._quote(msg)}")


class XonshMode(Mode):
    @classmethod
    @property
    def name(cls) -> str:
        return "xonsh"

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

    def _extend_path_impl(self, value: Union[str, Path], var_name: Optional[str]):
        # Assume extend_path function is provided by xonsh
        res = ["extend_path("]
        res.append(self._quote(value))
        if var_name is not None:
            res.append(f", {var_name!r}")
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

    def warning(self, msg: str):
        self._write(f"warning({self._quote(msg)})")


class FishMode(Mode):
    @classmethod
    @property
    def name(cls) -> str:
        return "fish"

    @classmethod
    @property
    def helper_path(cls) -> Path:
        return Path("shell_config/fish_helpers.fish")

    def eval_text(self, text: str):
        self._write("eval", self._quote(text))

    def source_file(self, f: Path):
        self._write("source", str(f))

    @classmethod
    @property
    def cleanup_code(cls) -> str:
        return "clear_helper_funcs\nset --erase clear_helper_funcs"

    def export(self, name: str, value: ShellValue):
        self._write(f"set -gx {name} {self._quote(value)}")

    def alias(self, name: str, value: ShellValue):
        # TODO: Do we ever need to quote the name?
        self._write(f"alias {name}={self._quote(value)}")

    def _extend_path_impl(self, value: Union[str, Path], var_name: Optional[str]):
        self._write(f"add_path_any --variable {var_name or 'PATH'}", self._quote(value))

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

    def warning(self, msg: str):
        self._write(f"warning {self._quote(msg)}")


_VALID_MODES = {
    "zsh": ZshMode(),
    "xonsh": XonshMode(),
    "fish": FishMode(),
}
for name, mode in _VALID_MODES.items():
    assert mode.name == name, mode.name


def run_mode(mode: Mode, config_file: Path) -> list[str]:
    assert not mode._output, "Already have output for mode"
    if (helper := mode.helper_path) is not None:
        mode.source_file(DOTFILES_PATH / helper)
    with open(config_file, "rt") as f:
        config_script = compile(f.read(), str(config_file), "exec")
    # TODO: Isolate to the specific module, not everything
    warnings.filterwarnings("default", category=DeprecationWarning)
    context = {
        "SHELL_BACKEND": mode.name,
    }
    for attr_name in dir(Mode):
        if attr_name.startswith("_"):
            continue
        context[attr_name] = getattr(mode, attr_name)
    exec(config_script, context, {})
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

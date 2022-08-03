#!/usr/bin/env python3
import re
import sys
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Optional, Type, Union

ShellValue = Union[Path, str, int, list["ShellValue"]]


class Mode(metaclass=ABCMeta):
    _output: list[str]

    def __init__(self):
        self._output = []
        self._defer_warnings = False

    def _write(self, *args: object):
        self._output.append(" ".join(map(str, args)))

    @abstractmethod
    def warning(self, msg: str):
        pass

    @abstractmethod
    def export(self, name: str, value: ShellValue):
        pass

    @abstractmethod
    def alias(self, name: str, value: ShellValue):
        pass

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
    def export(self, name: str, value: ShellValue):
        self._write(f"set -gx {name} {self._quote(value)}")

    def alias(self, name: str, value: ShellValue):
        # TODO: Do we ever need to quote the name?
        self._write(f"alias {name}={self._quote(value)}")

    def _extend_path_impl(self, value: Union[str, Path], var_name: Optional[str]):
        # TODO: Give warnings on missing paths
        if var_name is None:
            # Reuse that handy builtin
            self._write(f"fish_add_path -ga {self._quote(value)}")
        else:
            # This is adhoc
            self._write(f"if not contains {self._quote(value)} ${var_name}")
            self._write(f"    set -gxa {var_name} {self._quote(value)}")
            self._write("end")

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


def run_mode(mode: Mode, config_file: Path) -> list[str]:
    assert not mode._output, "Already have output for mode"
    with open(config_file, "rt") as f:
        config_script = compile(f.read(), str(config_file), "exec")
    context = {}
    for attr_name in dir(Mode):
        if attr_name.startswith("_"):
            continue
        context[attr_name] = getattr(mode, attr_name)
    exec(config_script, context, {})
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

#!/usr/bin/env python3
from __future__ import annotations

import functools
import os
import re
import runpy
import sys
import textwrap
import warnings
from abc import ABCMeta, abstractmethod
from contextlib import (
    AbstractContextManager,
    ExitStack,
    contextmanager,
    redirect_stdout,
)
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Final,
    Iterator,
    Literal,
    Optional,
    TypeAlias,
    Union,
    final,
)
from typing import get_args as get_type_args
from typing import get_origin as get_type_origin

# TODO: Once requiring 3.11 we can remove this
if TYPE_CHECKING:
    from typing_extensions import assert_never
else:

    def assert_never(val):
        raise AssertionError


SupportedColor: TypeAlias = Literal[
    # Matches _ANSI_COLOR_NAMES
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    # Special marker value
    "reset",
]

if TYPE_CHECKING:
    from typing import TypedDict

    # TODO: This is pointless now because we can't type kwargs...
    class FmtFlags(TypedDict, total=False):
        fg: bool
        foreground: bool
        bg: bool
        background: bool
        bold: bool
        italics: bool
        underline: bool

    class FmtInfo(TypedDict, total=False):
        color: SupportedColor


@functools.total_ordering  # TODO: Switch to my wrapper instead
class LogLevel(Enum):
    DEBUG = -1, {"color": "green", "italics": True}
    INFO = 0, {"color": "white", "bold": True}
    TODO = 1, {"color": "white", "bold": True, "italics": True}
    WARNING = 2, {"color": "yellow", "underline": True, "bold": True}

    def __new__(cls, level_id: int, fmt_info: FmtInfo):
        obj = object.__new__(cls)
        obj._value_ = level_id
        obj.level_id = level_id
        obj.fmt_info = fmt_info
        return obj

    def __lt__(self, other):
        if not isinstance(other, LogLevel):
            return NotImplemented
        return self.level_id < other.level_id

    # fields
    level_id: int
    fmt_info: FmtInfo

    DEFAULT_LEVEL: ClassVar[LogLevel]
    ENV_VAR_NAME: ClassVar[str]


LogLevel.DEFAULT_LEVEL = LogLevel.INFO
LogLevel.ENV_VAR_NAME = "SHELL_TRANS_LOG"


class VarAccess:
    __slots__ = "name"
    name: str

    def __eq__(self, other):
        return self.name == other.name if isinstance(other, VarAccess) else NotImplemented

    def __init__(self, name: str):
        self.name = name
        # Easier to ban than to handle ;)
        forbidden_chars = set(name) & {" ", "'", '"', "$"}
        if forbidden_chars:
            raise ValueError(f"Forbidden chars in {name!r} ({forbidden_chars!r})")

    def __str__(self) -> str:
        return f"${self.name}"


# TODO: why is list[ShellValue] permitted here?
StaticShellValue: TypeAlias = Path | str | int | list["StaticShellValue"]
ShellValue: TypeAlias = StaticShellValue | VarAccess | list["ShellValue"]


def resolve_static_shell_value(value: ShellValue) -> str:
    match value:
        case Path() | str(_) | int(_):
            return str(value)
        case VarAccess():
            raise TypeError(f"Cannot resolve a variable access statically: {value!r}")
        case list(_) as elements:
            return " ".join(resolve_static_shell_value(val) for val in elements)
        case _ as unreachable:
            if TYPE_CHECKING:
                assert_never(unreachable)
            else:
                raise TypeError(f"Expected a ShellValue: {unreachable!r}")


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

assert get_type_origin(SupportedColor) == Literal
assert get_type_args(SupportedColor) == (*_ANSI_COLOR_NAMES, "reset")

if (override_dotfiles_path := os.getenv("FORCE_OVERRIDE_DOTFILES_PATH")) is not None:
    # Provide a mechanism to bypass usage of `__file__` because that occasionally breaks
    DOTFILES_PATH = Path(override_dotfiles_path)
    assert DOTFILES_PATH.is_dir(), f"Missing dir: {DOTFILES_PATH}"
else:
    assert [p.name for p in Path(__file__).parents[:3]] == [
        "translate_shell",
        "dotfiles",
        "src",
    ]
    DOTFILES_PATH = Path(__file__).parents[3]
assert (DOTFILES_PATH / "src" / "dotfiles").is_dir(), "Missing $DOTFILES_PATH/src/dotfiles directory"


def which(command: str) -> Optional[Path]:
    """Alternate implementation of shutil.which"""
    path = os.getenv("PATH")
    if path is None:
        print("WARNING: Missing $PATH variable")
        return None
    for path_dir in map(Path, path.split(":")):
        actual = path_dir / command
        if os.access(actual, os.F_OK | os.X_OK):
            return actual
    return None


class ConfigException(BaseException):
    pass


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


class _Scope(Enum):
    EXPORT = "export"
    LOCAL = "local"
    ALIAS = "alias"


@dataclass
class ModeState:
    added_python_paths: list[Path] = field(default_factory=list)


class _AliasSpecialWraps(Enum):
    UPDATED = "updated"
    """Set to the updated command name"""
    ORIGINAL = "original"
    """Set to the original command name"""


AliasWrapsSetting: TypeAlias = str | _AliasSpecialWraps | None
"""
When defining a command alias, sets the "wraps" property.

Used primarily for the fish shell.
"""


class Mode(metaclass=ABCMeta):
    _output: list[str]
    _block_level: int
    _indent_level: int

    _state: Optional[ModeState]

    name: ClassVar[str]
    # Path to the helper functions
    helper_path: ClassVar[Optional[Path]] = None
    cleanup_code: ClassVar[Optional[str]] = None

    def __init__(self):
        self._output = []
        self._defer_warnings = False
        self._block_level = 0
        self._indent_level = 0
        self._indent = ""
        self._state = None

    @final
    def var(self, name: str) -> VarAccess:
        return VarAccess(name)

    def _write(self, *args: object):
        self._output.append(self._indent + " ".join(map(str, args)))

    @staticmethod
    def reset_color() -> str:
        """A command to reset the ANSI color codes. Equivalent to set_color('reset')"""
        return Mode.set_color("reset")

    @staticmethod
    def set_color(color: Optional[SupportedColor], **kwargs: bool) -> str:
        """
        Emits ANSI color codes to set the terminal color

        Tries to be consistent with click.style
        and fish set_style

        Valid keyword arguments option:
        bold - Sets bold color
        [...] - others
        fg, foreground - Sets the foreground color (implied by default)
        bg, background - Sets the background color
        """

        def check_flag(*names: str, default=False) -> bool:
            for name in names:
                if name not in kwargs:
                    continue
                val = kwargs[name]
                if not isinstance(val, bool):
                    raise TypeError(f"for {name!r}: {val!r}")
                return val  # type: ignore
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
        return "\x1b[" + ";".join(map(str, parts)) + "m"

    @final
    def exec_cmd(self, command: str, *args: ShellValue):
        self._write(command, *map(self._quote, args))

    @abstractmethod
    def eval_text(self, text: str):
        pass

    @abstractmethod
    def source_file(self, p: Path):
        pass

    @final
    @contextmanager
    def indent(self):
        self._indent_level += 1
        self._indent = " " * self._indent_level
        try:
            yield
        finally:
            self._indent_level -= 1
            self._indent = " " * self._indent_level

    @abstractmethod
    def block(self) -> AbstractContextManager[None]:
        pass

    @final
    def set_local(self, name: str, value: ShellValue, *, export: bool = True):
        self._assign(name, value, scope=_Scope.LOCAL, export=export)

    def _log(self, *msg: object, level: LogLevel, fmt: dict):
        if (enabled_level := getattr(self, "_log_level_enabled", None)) is None:
            enabled_level_name = os.getenv(  # type: ignore[call-overload]
                LogLevel.ENV_VAR_NAME, LogLevel.DEFAULT_LEVEL.name
            )
            try:
                enabled_level = LogLevel[enabled_level_name.upper()]
            except KeyError:
                # Avoid circular errors
                self._log_level_enabled = enabled_level = LogLevel.DEFAULT_LEVEL
                self.warning(f"Unknown log level name: {enabled_level_name!r} (env var ${LogLevel.ENV_VAR_NAME})")
            self._log_level_enabled = enabled_level
        assert enabled_level is not None
        if level < enabled_level:
            return
        assert fmt is not None
        print(
            "".join(
                (
                    self.set_color(**fmt),
                    level.name,
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
        res_funcs = {}
        log_fmt_info = [level.fmt_info for level in LogLevel]

        # dynamically initialize for each level
        for level, fmt_info in zip(LogLevel, log_fmt_info, strict=True):
            func_name = f"log_at_{level.name.lower()}"
            glbls = {
                "DEFAULT_FMT": fmt_info,
                "ChainMap": ChainMap,
                "LogLevel": LogLevel,
            }
            exec(
                textwrap.dedent(
                    f"""
                    def {func_name}(self, *msg: object, **custom_fmt):
                        if custom_fmt:
                            fmt=ChainMap(custom_fmt, DEFAULT_FMT)
                        else:
                            fmt = DEFAULT_FMT
                        self._log(*msg, level=LogLevel.{level.name}, fmt=fmt)
                    """
                ),
                glbls,
            )
            res_funcs[level] = glbls[func_name]

        return [res_funcs[level] for level in LogLevel]

    debug, info, todo, warning = _setup_log_levels()
    del _setup_log_levels  # avoid namespace pollution

    @abstractmethod
    def _assign(self, name: str, value: ShellValue, *, scope: _Scope, export: bool):
        pass

    @final
    def export(self, name: str, value: ShellValue):
        self._assign(name, value, scope=_Scope.EXPORT, export=True)

    ALIAS_WRAPS_UPDATED: Final[AliasWrapsSetting] = _AliasSpecialWraps.UPDATED
    ALIAS_WRAPS_ORIGINAL: Final[AliasWrapsSetting] = _AliasSpecialWraps.ORIGINAL

    def alias(
        self,
        name: str,
        value: ShellValue,
        *,
        wraps: AliasWrapsSetting,
        desc: str | None = None,
    ):
        _ = wraps, desc  # By default, just ignored
        self._assign(name, value, scope=_Scope.ALIAS, export=True)

    _REQUIRE_VAR_EQUALS_ERRMSG: ClassVar[str] = "Unexpected value for {varname}: `{actual_value}`"

    @abstractmethod
    def require_var_equals(self, name: str, value: ShellValue):
        """Requires that the specified variable has a specific value"""

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

    @final
    def extend_python_path(self, value: Union[str, Path]):
        self.debug(f"Adding python path: {value}")
        if not Path(value).is_dir():
            self.warning(f"Unable to find python path: {value!r}")
        self.require_state().added_python_paths.append(Path(value))
        self.extend_path(value, "PYTHONPATH", order=PathOrderSpec.APPEND)
        if str(value) not in sys.path:
            sys.path.append(str(value))

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
    def _extend_path_impl(self, value: str, var_name: Optional[str], *, order: PathOrderSpec):
        pass

    @abstractmethod
    def _quote(self, value: ShellValue) -> str:
        pass

    @final
    def require_state(self) -> ModeState:
        if self._state is None:
            raise AssertionError("Mode does not have state!")
        return self._state

    @final
    @contextmanager
    def with_state(self, new_state: ModeState | None = None) -> Iterator[ModeState]:
        if new_state is None:
            new_state = ModeState()
        assert self._state is None
        self._state = new_state
        try:
            yield new_state
            assert self._state is new_state
        finally:
            self._state = None

    # Names excluded from auto-export
    #
    # This is in addition to those starting with _
    AUTOEXPORT_EXCLUDE: ClassVar[set[str]] = {
        "AUTOEXPORT_EXCLUDE",
        "require_state",
        "with_state",
    }


# Things allowed without quoting
_ZSH_SIMPLE_QUOTE_PATTERN = re.compile(r"([\w_\-\/]+)")
# TODO: Is this ever any different?
_FISH_SIMPLE_QUOTE_PATTERN = _ZSH_SIMPLE_QUOTE_PATTERN


def escape_quoted(value: str, *, quote_char: str, bad_chars: set[str], simple_pattern: re.Pattern) -> str:
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

    def _assign(self, name: str, value: ShellValue, *, scope: _Scope, export: bool):
        flags = []
        if not export:
            match scope:
                case _Scope.LOCAL:
                    flags.append("-x")
                case _:
                    raise NotImplementedError
        self._write(scope.value, *flags, f"{name}={self._quote(value)}")

    @contextmanager
    def block(self):
        self._write("( # block")
        self._block_level += 1
        try:
            with self.indent():
                yield
        finally:
            self._block_level -= 1
            self._write(")")

    def require_var_equals(self, name: str, value: ShellValue):
        self._write(f'if test "${name}" != {self._quote(value)}; then')
        with self.indent():
            actual_value = "${" + name + "}"
            errmsg = Mode._REQUIRE_VAR_EQUALS_ERRMSG.format(varname=name, actual_value=actual_value)
            self._write(f'warning "{errmsg}"')
        self._write("fi")

    def _extend_path_impl(self, value: str, var_name: Optional[str], *, order: PathOrderSpec):
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
        if isinstance(value, (int, VarAccess)):
            return str(value)
        elif isinstance(value, (str, Path)):
            value = str(value)
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


class _XonshBlock:
    local_vars: set[str]

    def __init__(self):
        self.local_vars = set()


class XonshMode(Mode):
    name: ClassVar = "xonsh"
    _ast_mod: ClassVar[Any] = None
    _blocks: list[_XonshBlock]

    def __init__(self):
        super().__init__()
        self._blocks = []

    def eval_text(self, text: str):
        self._write(f"execx({self._quote(text)})")

    def source_file(self, p: Path):
        # Not needed because xonsh currently has no helpers
        #
        # Once we do implement this, it should probably down to
        # a from `{f}` import *
        #
        # TODO: This is actually very hard because of namespacing
        # We want separate modules, but then what happens to results?
        #
        # Need a better system...
        raise NotImplementedError

    def _assign(self, name: str, value: ShellValue, *, scope: _Scope, export: bool):
        target: str
        if scope != _Scope.LOCAL and not export:
            raise NotImplementedError
        match scope:
            case _Scope.EXPORT:
                target = f"${name}"
            case _Scope.LOCAL:
                target = f"${name}" if export else name
            case _Scope.ALIAS:
                target = f"aliases[{name!r}]"
            case _:
                raise NotImplementedError
        if scope == _Scope.LOCAL and export:
            self._blocks[-1].local_vars.add(name)
        self._write(target, "=", self._quote(value))

    def require_var_equals(self, name: str, value: ShellValue):
        XonshMode._validate_python_name(name)
        self._write()
        self._write(f"if ${name} != {self._quote(value)}:")
        with self.indent():
            actual = f"${name}"
            errmsg = Mode._REQUIRE_VAR_EQUALS_ERRMSG.format(varname=name, actual_value=actual)
            self._write(f"warning({errmsg})")
        self._write()

    @staticmethod
    def _validate_python_name(name: str):
        if TYPE_CHECKING:
            import ast
        else:
            ast = XonshMode._ast_mod
            if ast is None:
                del ast
                import ast

                XonshMode._ast_mod = ast
        try:
            expr_body = ast.parse(name, mode="eval").body
            if not isinstance(expr_body, ast.Name):
                raise TypeError(f"Expected ast.Name: {type(expr_body)}")
        except (SyntaxError, TypeError):
            raise ValueError(f"Not a valid python name: {name}")

    @contextmanager
    def block(self):
        self._write()
        self._write("def _block():")
        self._blocks.append(block := _XonshBlock())
        self._block_level += 1
        try:
            with self.indent():
                yield
        finally:
            assert self._block_level == len(self._blocks)
            assert self._blocks[-1] is block
            self._blocks.pop()
            self._block_level -= 1
            self._write("_block()")
            for local in block.local_vars:
                self._write(f"del ${local}")
            self._write("del _block")
            self._write()

    def _extend_path_impl(self, value: Union[str, Path], var_name: Optional[str], *, order):
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
        if isinstance(value, (int, VarAccess)):
            return str(value)
        elif isinstance(value, (str, Path)):
            value = str(value)
        elif isinstance(value, list):
            return "[" + ", ".join(map(self._quote, value)) + "]"
        else:
            raise TypeError(type(value))
        # xonsh is Python
        assert isinstance(value, str)
        return repr(value)


class FishMode(Mode):
    name: ClassVar = "fish"
    # TODO: This is a hack
    helper_path: ClassVar = Path(__file__).parent / "fish_helpers.fish"
    cleanup_code: ClassVar = "clear_helper_funcs\nset --erase clear_helper_funcs"

    def eval_text(self, text: str):
        self._write("eval", self._quote(text))

    def source_file(self, f: Path):
        self._write("source", str(f))

    def _assign(self, name: str, value: ShellValue, *, scope: _Scope, export: bool):
        value = self._quote(value)
        set_scope = None
        match scope:
            case _Scope.EXPORT:
                set_scope = "--global"
            case _Scope.LOCAL:
                assert self._block_level > 0
                set_scope = "--local"
            case _Scope.ALIAS:
                raise ValueError("Should not be reachable! (handled in assign)")
        if set_scope is None:
            raise AssertionError
        flags = [set_scope]
        if export:
            flags.append("--export")
        elif scope != _Scope.LOCAL:
            raise NotImplementedError
        self._write("set", *flags, name, value)

    def alias(
        self,
        name: str,
        value: ShellValue,
        *,
        wraps: AliasWrapsSetting,
        desc: str | None = None,
    ):
        wraps_cmd: str | None
        match wraps:
            case None:
                wraps_cmd = None
            case _AliasSpecialWraps.ORIGINAL:
                wraps_cmd = name
            case _AliasSpecialWraps.UPDATED:
                wraps_cmd = resolve_static_shell_value(value)
            case str(specific_wraps_val):
                wraps_cmd = specific_wraps_val
            case _ as unreachable:
                if TYPE_CHECKING:
                    assert_never(unreachable)
                raise TypeError
        # infer a description
        if desc is None:

            def is_allowed_complexity(inferred_desc: str) -> bool:
                for forbidden in ("\n", "&&"):
                    if forbidden in inferred_desc:
                        return False
                return len(inferred_desc) < 40

            inferred_descriptions: list[str] = []
            if wraps_cmd is not None:
                inferred_descriptions.append(f"alias {name} wraps {wraps_cmd}")
            inferred_descriptions.append(f"alias {name}={self._quote(value)}")
            for inferred_desc in inferred_descriptions:
                if is_allowed_complexity(inferred_desc):
                    desc = inferred_desc
                    assert desc is not None
            # the inferred descriptions were complex
            if desc is None:
                desc = f"alias for {name} (very complex definition)"
        # flags to the `function` command
        flags: list[str] = [f"--description {self._quote(desc)}"]
        if wraps_cmd is not None:
            flags.append(f"--wraps {self._quote(wraps_cmd)}")
        # define the actual alias
        definition_lines = [f"function {name}"]
        indent = " " * 4
        for flag in flags:
            definition_lines[-1] += " \\"
            definition_lines.append(indent * 2 + flag)
        definition_lines.extend((f"{indent}{value} $argv", "end"))
        for line in definition_lines:
            self._write(line)

    def require_var_equals(self, name: str, value: ShellValue):
        self._write(f'if test "${name}" != {self._quote(value)};')
        with self.indent():
            actual = f"${name}"
            errmsg = Mode._REQUIRE_VAR_EQUALS_ERRMSG.format(varname=name, actual_value=actual)
            self._write(f'warning "{errmsg}"')
        self._write("end")

    @contextmanager
    def block(self):
        self._block_level += 1
        self._write("begin")
        try:
            with self.indent():
                yield
        finally:
            self._block_level -= 1
            self._write("end")

    def _extend_path_impl(self, value: Union[str, Path], var_name: Optional[str], *, order: PathOrderSpec):
        self._write(
            f"add_path_any --variable {var_name or 'PATH'} {order.fish_flag}",
            self._quote(value),
        )

    def _quote(self, value: ShellValue) -> str:
        if isinstance(value, (int, VarAccess)):
            return str(value)
        elif isinstance(value, (Path, str)):
            value = str(value)
        elif isinstance(value, list):
            assert value, "Empty lists are forbidden"
            # lists are really fundamental in fish, all variables are arrays
            # thus, we just have to space-separate the quoted variables
            return " ".join(map(self._quote, value))
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
                # Check for X11 installation
                return which("Xorg") is not None
            case Platform.MAC_OS:
                return True  # consider macs always desktops ;)
            case _:
                raise UnsupportedPlatformError(self)

    def __str__(self) -> str:
        return self.name.lower().replace("_", "")


class AppDir(Enum):
    USER_CONFIG = "~/.config"
    USER_DATA = "~/.local/share"

    def resolve(self, platform: Platform) -> Path:
        path: Path
        match (platform, self):
            case (Platform.LINUX, _):
                # linux is easy (designed that way)
                path = Path(self.value).expanduser()
            case (Platform.MAC_OS, AppDir.USER_CONFIG) | (
                Platform.MAC_OS,
                AppDir.USER_DATA,
            ):
                path = Path.home() / "Library/Application Support"
            case _:
                raise UnsupportedPlatformError(platform, f"Unknown directory {self}")
        if not path.is_dir():
            raise FileNotFoundError(f"Expected {self} at {str(path)!r}")
        else:
            return path


_VALID_MODES: dict[str, type[Mode]] = {
    "zsh": ZshMode,
    "xonsh": XonshMode,
    "fish": FishMode,
}
for name, mode in _VALID_MODES.items():
    assert mode.name == name, mode.name


def run_mode(mode: Mode, module_name: str) -> list[str]:
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
        "UnsupportedPlatformError": UnsupportedPlatformError,
        "which": which,
        # TODO: This is a hack needed for support.macapp
        "_MODE_IMPL": mode,
    }
    for attr_name in dir(Mode):
        if attr_name.startswith("_") or attr_name in Mode.AUTOEXPORT_EXCLUDE:
            continue
        context[attr_name] = getattr(mode, attr_name)
    # stdout is only for translation output, not messages
    with redirect_stdout(sys.stderr):
        with mode.with_state() as state:
            runpy.run_module(
                module_name,
                init_globals=context,
                alter_sys=True,
            )
            # If python paths were added inside script,
            # extend them to outer context
            #
            # TODO: Instead, tell runpy not to reset sys.path
            for added_path in state.added_python_paths:
                if str(added_path) not in sys.path:
                    sys.path.append(str(added_path))
        # Cleanup
    if (cleanup := mode.cleanup_code) is not None:
        for line in cleanup.splitlines():
            mode._write(line)
    return mode._output


def main():
    remaining_args = sys.argv[1:]

    def consume_arg(*, amount: Optional[int] = None) -> str | list[str]:
        if amount is None:
            return remaining_args.pop(0)
        else:
            consumed = remaining_args[:amount]
            del remaining_args[:amount]
            return consumed

    def require_arg(flag_name: str) -> str:
        try:
            return remaining_args[1]
        except IndexError:
            print(f"Expected an argument to {flag_name} flag", file=sys.stderr)
            sys.exit(1)

    mode_type = None
    in_modules = []
    out_files = []
    while remaining_args and (flag := remaining_args[0]).startswith("-"):
        match flag:
            case "--":
                consume_arg()
                break  # Done processing flags
            case "--mode":
                if mode_type is not None:
                    print("Cannot specify --mode twice", file=sys.stderr)
                    sys.exit(1)
                mode_name = require_arg("--mode")
                try:
                    mode_type = _VALID_MODES[mode_name]
                except KeyError:
                    print(f"Invalid mode: {mode_name}", file=sys.stderr)
                    sys.exit(1)
                else:
                    consume_arg(amount=2)
            case "--mod-path":
                mod_path = Path(require_arg("--mod-path"))
                if not mod_path.is_dir():
                    print(f"ERROR: Missing module path: {mod_path}", file=sys.stderr)
                    sys.exit(1)
                if str(mod_path) not in sys.path:
                    sys.path.append(str(mod_path))
                consume_arg(amount=2)
            case "--module" | "-m":
                in_modules.append(mod_name := require_arg("--module"))
                if "/" in mod_name:
                    print(
                        "".join(
                            (
                                Mode.set_color("fellow"),
                                "WARNING",
                                Mode.reset_color(),
                                ":",
                            )
                        ),
                        f"Unexpected character `/` in module name: {mod_name!r}",
                        file=sys.stderr,
                    )
                consume_arg(amount=2)
            case "--out" | "-o":
                out_files.append(Path(require_arg("--out")))
                consume_arg(amount=2)
            case _:
                print(f"Unexpected flag: {flag!r}", file=sys.stderr)
                sys.exit(1)

    if len(in_modules) == 0:
        print("ERROR: Got no input modules", file=sys.stderr)
        sys.exit(1)

    if len(in_modules) == 1 and len(out_files) == 0:
        # With only one in file (and no explicit output), write to stdout
        out_files.append(sys.stdout)

    if len(in_modules) != len(out_files):
        print(
            f"Expected {len(out_files)} outputs for {len(in_modules)} inputs",
            file=sys.stderr,
        )
        sys.exit(1)

    for in_mod, out_file in zip(in_modules, out_files, strict=True):
        # Avoid contextlib due to potential for longer import times
        with ExitStack() as stack:
            if isinstance(out_file, Path):
                out_file_handle = stack.enter_context(open(out_file, "wt"))
            else:
                out_file_handle = out_file
            mode = mode_type()  # Construct mode object
            for line in run_mode(mode, in_mod):
                print(line, file=out_file_handle)


if __name__ == "__main__":
    main()

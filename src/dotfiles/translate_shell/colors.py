"""Support for ANSI terminal colors/formats"""
from __future__ import annotations

import inspect
import types
import dataclasses
import operator
from dataclasses import dataclass, field, InitVar
from typing import TYPE_CHECKING, TypeVar
from enum import Enum, nonmember
from functools import cached_property, cache

if TYPE_CHECKING:
    from typing import TypedDict, ClassVar, assert_type, Self, Any, Callable, final
    from collections.abc import Mapping

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
else:
    def final(cls):
        return cls

class SupportedColor(Enum):
    BLACK = "black"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"
    RESET = None
    """Special marker value indicating the formatting should be cleared"""

    @cached_property
    def _code_offset(self) -> int | None:
        match self.value:
            case None:
                return None
            case str(_name):
                return assert_type(list(SupportedColor), list[SupportedColor]).index(self)
            case _:
                raise TypeError

class FmtTarget(Enum):
    """Whether to apply the formatting to the foreground or background"""
    FOREGROUND = "fg"
    BACKGROUND = "bg"


@dataclass(kw_only=True, frozen=True)
@final
class FmtFlags:
    target: FmtTarget = field(init=False)
    bold: bool = False
    italics: bool = False
    underline: bool = False
    # Aliases which specify the `target`
    foreground: InitVar[bool] = False
    fg: InitVar[bool] = False
    background: InitVar[bool] = False
    bg: InitVar[bool] = False
    # static defaults
    _DEFAULT_TARGET: ClassVar[FmtTarget] = FmtTarget.FOREGROUND
    DEFAULT: ClassVar[FmtFlags]

    _TARGET_FLAG_NAMES: ClassVar[tuple[str, ...]] = ("foreground", "fg", "background", "bg")

    def __post_init__(self, foreground: bool, fg: bool, background: bool, bg: bool) -> None:
        target_flags: tuple[bool, ...] = (foreground, fg, background, bg)
        target_flag_names: tuple[str, ...] = FmtFlags._TARGET_FLAG_NAMES
        FmtFlags._verify_setup_signature(self.__post_init__)
        enabled_targets: set[FmtTarget] = set()
        for name, is_enabled in zip(target_flag_names, target_flags, strict=True):
            if is_enabled:
                enabled_targets.add(name)
        target: FmtTarget
        match enabled_targets:
            case ():
                target = FmtFlags._DEFAULT_TARGET
            case (desired_target,):
                target = desired_target
            case set(multiple):
                raise ValueError(f"Cannot specify multiple target aliases: {multiple!r}")
            case _:
                raise AssertionError
        object.__setattr__(self, 'target', target)

    @classmethod
    def _verify_setup_signature(cls: type[Self], setup_func: Callable[[...], None]) -> None:
        target_flag_names = FmtFlags._TARGET_FLAG_NAMES
        # names of parameters to this method
        param_names: list[str] = list(inspect.signature(setup_func).parameters.keys())
        first_param_index = param_names.index(target_flag_names[0])
        actual_flag_names = param_names[first_param_index:first_param_index + len(target_flag_names)]
        if actual_flag_names != FmtFlags._TARGET_FLAG_NAMES:
            raise AssertionError
        # Only verify once, disabling future calls
        cls._verify_setup_signature = lambda _func: None

    @property
    def is_default(self) -> bool:
        return self == FmtFlags._DEFAULT_TARGET

    @cache
    def custom_flags(self) -> set[str]:
        field_info: tuple[dataclasses.Field, ...] = dataclasses.fields(self)
        _flag_set = set()
        def add_flag(name: str) -> None:
            assert name not in _flag_set, f"Duplicate name: {name!r}"
            _flag_set.add(name)

        for field in field_info:
            value = getattr(self, field.name)
            default_value = getattr(FmtFlags.DEFAULT, field.name)
            if value == default_value:
                continue
            match default_value:
                case False:
                    add_flag(field.name)
                case FmtTarget(_):
                    assert default_value == FmtFlags._DEFAULT_TARGET
                    assert isinstance(value, FmtTarget)
                    add_flag(value.name.lower())
                case _:
                    raise AssertionError(f"Unexpected default value {default_value!r} for {field.name!r}")
        return _flag_set

    def __repr__(self):
        flags = self.custom_flags()
        if flags:
            res = ["FmtFlags("]
            for i, flag in enumerate(flags):
                if i > 0:
                    res.append(", ")
                res.append(flag)
                res.append("=True")
            res.append(")")
            return ''.join(res)
        else:
            return "FmtFlags.DEFAULT"

FmtFlags.DEFAULT = FmtFlags()
assert FmtFlags.DEFAULT.is_default
# Test non-default flags
assert FmtFlags(bold=True).custom_flags() == {"bold"}
assert FmtFlags(italics=True, bold=True, bg=True).custom_flags() == {"bold", "italics", "background"}
repr(FmtFlags(bold=True))

def reset_code():
    return format_code(color=SupportedColor.RESET)

def format_code(color: SupportedColor, flags: FmtFlags = FmtFlags()) -> str:
    """
    Emits ANSI color codes to set the terminal color

    Tries to be consistent with click.style
    and fish set_style
    """
    if not isinstance(flags, FmtFlags):
        raise TypeError
    # https://talyian.github.io/ansicolors/
    # https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters
    parts = []
    match color:
        case SupportedColor.RESET:
            if flags != FmtFlags.DEFAULT:
                raise ValueError(f"All custom flags are incompatible with reset: {FmtFlags.DEFAULT}")
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

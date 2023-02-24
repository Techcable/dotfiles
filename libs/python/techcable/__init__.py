"""My utility libraries..."""
from __future__ import annotations
from abc import ABC, ABCMeta
import importlib
import inspect
import os
import sys
from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    ForwardRef,
    Optional,
    TypeAlias,
    TypeGuard,
    TypeVar,
    final,
    ClassVar,
    Never,
    runtime_checkable,
    overload,
    Literal,
)
import functools
import operator

if TYPE_CHECKING:
    # new in 3.11
    import types
    from typing import dataclass_transform
else:

    def dataclass_transform(**kwargs):
        return lambda x: x


__all__ = ("PlatformPath", "PlatformError", "define_order", "MISSING")


assert isinstance(None, MarkerValue)


def is_marker(value: Any) -> TypeGuard[MarkerValue]:
    """Check if the specified value is a marker value"""
    return isinstance(value, MarkerValue)


@final
class Missing:
    """
    Reprsents a singleton missing value

    Retreivable via techcable.MISSING
    """

    def __init__(self):
        raise TypeError(f"{MISSING!r} is a singleton!")

    def __repr__(self) -> str:
        return "techcable.MISSING"

    def __str__(self) -> str:
        return f"{self!r} (marker value)"

    def __bool__(self) -> bool:
        return False

    @staticmethod
    def test(val: Any) -> bool:
        """
        Test if the specified value is MISSING

        Equivalent to `lambda x: x is MISSING`, useful in functional chaining.
        However, more efficiently implemented to avoid global lookup
        """
        raise AssertionError  # Note: Overriden later

    @staticmethod
    def test_not(val: Any) -> bool:
        """
        Test if the specified value is *not* MISSING

        This is the opposite of Missing.TEST

        Equivalent to `lambda x: x is not MISSING`, useful in functional chaining.
        However, more efficiently implemented to avoid global lookup
        """
        raise AssertionError  # Note: Overriden later

    VALUE: ClassVar[Missing]
    """The singleton value. An alias for MISSING"""


MissingOrNone: TypeAlias = Missing | None

MISSING: Final[Missing] = object.__new__(Missing)
"""Marker value for missing values"""

Missing.VALUE = MISSING


if not TYPE_CHECKING:
    Missing.test = partial(
        operator.is_,
    )


class PlatformPath(Enum):
    HOMEBREW_PREFIX = ("darwin", "HOMEBREW_PREFIX")

    def __init__(self, platform: str | None, env_var: str):
        super().__init__()
        self.required_platform = platform
        self._env_var = env_var
        self._cached_value = MISSING

    def try_resolve(self) -> Path | None:
        try:
            return self._cached_value  # type: ignore
        except AttributeError:
            pass
        try:
            return self.resolve()
        except (PlatformError, FileNotFoundError):
            self._cached_value = None  # type: ignore
            return None

    def resolve(self) -> Path:
        if getattr(self, "_cached_value", None) is not None:
            return self._cached_value  # type: ignore
        if (
            self.required_platform is not None
            and self.required_platform != sys.platform
        ):
            raise PlatformError(
                f"Expected platform {self.required_platform}, but got {sys.platform}"
            )
        assert self._env_var is not None
        res = os.getenv(self._env_var)
        if res is None:
            raise PlatformError(
                "Missing expected environment variable {self._env.var} for {self}"
            )
        path = Path(res)
        self._cached_value = path  # type: ignore
        return path

    def exists(self) -> bool:
        return (path := self.try_resolve()) is not None and path.exists()

    def __bool__(self):
        return self.try_resolve() is not None

    def __str__(self):
        return f"{self.name}({self.try_resolve()})"


class PlatformError(OSError):
    pass


T = TypeVar("T")


@dataclass_transform(order_default=True, eq_default=True)
def define_order(
    tp: type[T], *, unsafe_eq: bool = False, keys: Sequence[str]
) -> type[T]:
    if is_dataclass(tp):
        raise TypeError("Must invoke @define_order *before* @dataclass")
    if tp.__eq__ != object.__eq__ and safe_eq:
        raise TypeError(
            f"Custom equals method `{tp.__name__}.__eq__` is unsafe! (Specify `unsafe_eq` to ignore this)"
        )
    keys = tuple(dict.fromkeys(keys).keys())  # ensure unique
    match len(key):
        case 0:
            raise TypeError("Need at least one key!")
        case 1:
            single_key = keys[0]
            assert single_key, "Key name cannot be empty"
        case _:
            assert all(key in keys), "Key names cannot be empty"
            single_key = None

    type_const = tp.__name__

    def blanks(amount: int) -> tuple[str, ...]:
        assert amount > 0
        return ("",) * amount

    def gen_operator(
        op_name: str, *, strict: str, relaxed: str | None, logic_op: str = "and"
    ) -> Iterator[str]:
        if relaxed is None:
            relaxed = strict
        assert not op_name.startswith("__")
        yield f"def {op_name}(self, other) -> bool:",
        yield f"  if not isinstance(other, {type_const}):",
        yield "     return NotImplemented",
        yield "  return ("
        for key in keys:
            indent = "  " * 3
            if key != keys[-1]:
                # not last
                yield f"{indent}self.{key} {op_text_relaxed} other.{key} {logic_op}"
            else:
                # last
                yield f"{indent}self.{key} {op_text_strict} other.{key}"
        yield "  )"
        yield from blanks(2)
        yield f"{type_const}.__{op_name}__ = {op_name}"

    res = [
        *gen_operator("eq", strict="==", relaxed=None),
        *gen_operator("ne", strict="!=", relaxed=None, logic_op="or"),
        *gen_operator("lt", strict="<", relaxed="<="),
        *gen_operator("le", strict="<=", relaxed=None),
        *gen_operator("gt", strict=">", relaxed=">="),
        *gen_operator("ge", strict=">=", relaxed=None),
    ]
    exec("\n".join(res), globals=__builtins__, locals={type_const: tp})

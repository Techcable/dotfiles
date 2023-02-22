"""My utility libraries..."""
import importlib
import inspect
import os
import sys
from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Final, Optional, TypeVar, final

if TYPE_CHECKING:
    # new in 3.11
    import types
    from typing import dataclass_transform
else:

    def dataclass_transform(**kwargs):
        return lambda x: x


__all__ = ("PlatformPath", "PlatformError", "define_order", "MISSING")


@final
class _Missing:
    def __repr__(self):
        return "techcable.MISSING"

    def __str__(self):
        return f"{self!r} (marker value)"


MISSING: Final[object] = _Missing()
"""Marker value for missing values"""


class PlatformPath(Enum):
    HOMEBREW_PREFIX = ("darwin", "HOMEBREW_PREFIX")

    def __init__(self, platform: str | None, env_var: str):
        super().__init__(self.name)
        self.required_platform = platform
        self._env_var = env_var

    def try_resolve(self) -> Path | None:
        try:
            return self._cached_value
        except AttributeError:
            pass
        try:
            return self.resolve()
        except (PlatformError, FileNotFoundError):
            self._cached_value = None
            return None

    def resolve(self) -> Path:
        if getattr(self, "_cached_value", None) is not None:
            return self._cached_value
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
        path = self._cached_value = Path(res)
        return path

    def exists(self) -> bool:
        return (path := self.try_resolve()) is not None and path.exists()

    def __bool__(self):
        return self.try_resolve() is not None

    def __str__(self):
        return f"{self.name}({self._try_resolve()})"


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

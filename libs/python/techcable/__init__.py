"""My utility libraries..."""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Sequence
from dataclasses import is_dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator, TypeVar

if TYPE_CHECKING:
    from itertools import chain

    # new in 3.11
    from typing_extensions import dataclass_transform
else:
    chain = None

    def dataclass_transform(**kwargs):
        return lambda x: x


__all__ = (
    "PlatformPath",
    "PlatformError",
    "define_order",
    "MISSING",
    "Missing",
)

if __debug__:
    from . import _missing

    assert _missing.__all__ == ("MISSING", "Missing")
from ._missing import MISSING, Missing


# TODO: Move to seperate module
class PlatformPath(Enum):
    HOMEBREW_PREFIX = ("darwin", "HOMEBREW_PREFIX")

    def __init__(self, platform: str | None, env_var: str):
        super().__init__()
        self.required_platform = platform
        self._env_var = env_var

    def try_resolve(self) -> Path | None:
        val = self._cached_value
        if val is not MISSING:
            return val
        try:
            return self.resolve()
        except (PlatformError, FileNotFoundError):
            self._cached_value = None
            return None

    def resolve(self) -> Path:
        if getattr(self, "_cached_value", None) is not None:
            return self._cached_value  # type: ignore
        if self.required_platform is not None and self.required_platform != sys.platform:
            raise PlatformError(f"Expected platform {self.required_platform}, but got {sys.platform}")
        assert self._env_var is not None
        res = os.getenv(self._env_var)
        if res is None:
            raise PlatformError(f"Missing expected environment variable {self._env_var} for {self}")
        path = Path(res)
        self._cached_value = path  # type: ignore
        return path

    def exists(self) -> bool:
        return (path := self.try_resolve()) is not None and path.exists()

    def __bool__(self):
        return self.try_resolve() is not None

    def __str__(self):
        return f"{self.name}({self.try_resolve()})"

    _cached_value: Path | Missing | None


class PlatformError(OSError):
    pass


T = TypeVar("T")


@dataclass_transform(order_default=True, eq_default=True)
def define_order(*, unsafe_eq: bool = False, keys: Sequence[str]) -> Callable[[type[T]], type[T]]:
    global chain
    if not TYPE_CHECKING and chain is None:
        chain = importlib.import_module("itertools").chain
    keys = tuple(dict.fromkeys(keys).keys())  # ensure unique
    single_key: str | None
    match len(keys):
        case 0:
            raise TypeError("Need at least one key!")
        case 1:
            single_key = keys[0]
            assert single_key, "Key name cannot be empty"
        case _:
            assert all(keys), "Key names cannot be empty"
            single_key = None

    def blanks(amount: int) -> tuple[str, ...]:
        assert amount > 0
        return ("",) * amount

    def gen_operator(op_name: str, *, strict: str, relaxed: str | None, logic_op: str = "and") -> Iterator[str]:
        if relaxed is None:
            relaxed = strict
        assert not op_name.startswith("__")
        yield f"def {op_name}(self, other) -> bool:"
        yield "  if not isinstance(other, TargetType):"
        yield "     return NotImplemented"
        yield "  return ("
        for key in keys:
            indent = "  " * 3
            if key != keys[-1]:
                # not last
                yield f"{indent}self.{key} {relaxed} other.{key} {logic_op}"
            else:
                # last
                yield f"{indent}self.{key} {strict} other.{key}"
        yield "  )"
        yield from blanks(2)
        yield f"TargetType.__{op_name}__ = {op_name}"

    modifying_text = "\n".join(
        chain(
            gen_operator("eq", strict="==", relaxed=None),
            gen_operator("ne", strict="!=", relaxed=None, logic_op="or"),
            gen_operator("lt", strict="<", relaxed="<="),
            gen_operator("le", strict="<=", relaxed=None),
            gen_operator("gt", strict=">", relaxed=">="),
            gen_operator("ge", strict=">=", relaxed=None),
        )
    )

    def transform(tp: type[T]) -> type[T]:
        if is_dataclass(tp):
            raise TypeError("Must invoke @define_order *before* @dataclass")
        if tp.__eq__ != object.__eq__ and not unsafe_eq:
            raise TypeError(
                f"Custom equals method `{tp.__name__}.__eq__` is unsafe! (Specify `unsafe_eq` to ignore this)"
            )

        # Modifies type in-place
        exec(modifying_text, {"TargetType": tp}, None)

        return tp

    return transform

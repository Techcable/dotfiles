"""Metadata about errors"""
from __future__ import annotations
from abc import ABC, ABCMeta
from ast import Attribute

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Literal, Never, NewType, TypeAlias, TypeVar, overload
if TYPE_CHECKING:
    import dis
    import types

# NOTE: Must not depend on parent module
from .. import MISSING, MissingOrNone

@dataclass(slots=True, frozen=True)
class MetaValue(metaclass=ABCMeta):
    key: MetaKey = field(init=False)

@dataclass(slots=True, frozen=True)
class SourceValue(MetaValue):
    text: str
    location: Position | MissingMetaReason

class MissingMetaReason(Enum):
    DISABLED = "was disabled"
    FRAME_ERROR = "error loading frame"
    SOURCE_READ_ERROR = "error reading source"
    LOCATION_READ_ERROR = "error detecting location"

    @property
    def is_error(self) -> bool:
        return 'ERROR' in self.name

    @property
    def message(self) -> str:
        return self.value

class MetaKey(Enum):
    CONDITION = str
    VALUE = str

    def __init__(self):
        super().__init__()
        self._field_name = self.name.lower()


@dataclass(frozen=True, slots=True)
class InternalMeta:
    condition: SourceValue | MissingMetaReason | None
    value: SourceValue | MissingMetaReason | None

    @overload
    def __getitem__(self, key: MetaKey) -> MetaValue:
        pass

    @overload
    def __getitem__(self, key: object) -> Never:
        pass

    def __getitem__(self, key):
        if isinstance(key, MetaKey):
            field_name = key._field_name
        else:
            raise TypeError(f"Expected a MetaKey, got {type(key)}")
        try:
            res = getattr(self, field_name)
        except AttributeError:
            raise KeyError("Internal error: Unexpected MetaKey {key.name}")
            

    @staticmethod
    def load():





@dataclass(frozen=True)
class Position:
    __slots__ = ""
    code: BytecodePosition

    @property
    def source(self) -> SourcePosition | MissingMetaReason:
        return self._source
    

    def __setattr_()

@dataclass(frozen=True, slots=True)
class BytecodePosition:
    code_object: types.CodeType
    bytecode_idx: int

@dataclass(frozen=True, slots=True)
class SourcePosition:
    raw: BytecodePosition



def resolve_frame(frame: FrameType | int) -> :

def detect_condition(, _frame:  | int) -> str:
    pass

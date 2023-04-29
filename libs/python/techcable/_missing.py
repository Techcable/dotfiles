"""The singleton `techcable.MISSING` value"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from enum import Enum
    from typing import ClassVar, Final, Literal

    # TYPE_CHECKING needs Enum so that we can use typing.Literal
    _MissingBase = Enum
else:
    _MissingBase = object


@final
class Missing(_MissingBase):
    """The type of the singleton `techcable.MISSING` value`"""

    if not TYPE_CHECKING:
        VALUE = None
    else:
        VALUE: ClassVar[Missing]
        """An alias for techcable.MISSING"""

    def __new__(cls):
        global MISSING
        raise TypeError("Unable to create new instances of {MISSING}")

    def __repr__(self):
        return "techcable.MISSING"

    def __bool__(self) -> Literal[False]:
        return False


if not TYPE_CHECKING:
    Missing.VALUE = object.__new__(Missing)


# Need typing.Literal so we can have `val is not MISSING`
MISSING: Final[Literal[Missing.VALUE]] = Missing.VALUE
"""Marker value for missing values"""

__all__ = (
    "MISSING",
    "Missing",
)
assert sorted(__all__) == list(__all__)

from __future__ import annotations

from typing import Literal, Never, TYPE_CHECKING
if TYPE_CHECKING:
    import dis

from .. import Missing, MissingOrNone

from . import InternalError

class VerifyError(InternalError):
    """Indicates that internal invariants have been violated"""
    def __init__(self, *args, condition: str, value: str | None, loc: dis.Positions | MissingOrNone):
        super().__init__(*args)

    

@overload
def verify_not(value: None, is_none: Literal[None]) -> Never:
    raise VerifyError()

T = TypeVar('T')


@overload
def verify_not(value: VT, is_none: Literal[None]) -> :
    pass

@overload
def verify_not(value: VT, tp: type) -> :


VerifyCallback: TypeAlias = Callable[[], str | VerifyError]
def verify(cond: bool, msg: str | Callable[], *, cond_text: str | None | MISSING) -> :

def detect_param()
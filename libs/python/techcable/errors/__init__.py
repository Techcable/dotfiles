from typing import TYPE_CHECKING, ClassVar, Never, assert_never, overload, Literal, TypeVar

from .meta import InternalMeta

class InternalError(AssertionError, RuntimeError):
    """
    Indicates an internal runtime error has occurred,
    triggered by an unexpected bug.

    This is in contrast to other errors,
    which may be triggered by user mistakes/system failure.
    """
    DEFAULT_MSG: ClassVar[str] = "internal error"

    meta: InternalMeta

    def __init__(self, msg: str | None=None, *args, msg_prefix: str | None=None, default_msg: str=DEFAULT_MSG):
        explicit_msg = msg
        del msg
        match (explicit_msg, msg_prefix, default_msg):
            case (str(custom), str(prefix), _):
                msg = f"{custom}: {prefix}"
            case (str(custom), None, _):
                msg = custom
            case (None, None | str(_), str(def_msg)):
                msg = def_msg
            case (None, str(prefix), None):
                msg = prefix
            case (None, None, None):
                raise TypeError(f"Must specify a message for {type(self)}: defaults are None")
            case _ as unreachable:
                assert_never(unreachable)


class UnreachableError(InternalError):
    """
    Thrown when an unreachable code path is unexpectedly hit.

    See method UNREACHABLE()
    """
    def __init__(self, msg: str | None=None, *args, **kwargs):
        if msg is None:
            msg = UnreachableError.MSG_PREFIX
        else:
            msg = f'{UnreachableError.MSG_PREFIX}: {msg}'
        super().__init__(msg, *args, **kwargs, msg_prefix="")

    MSG_PREFIX: ClassVar[str] = "entered unreachable code"

class TodoError(RuntimeError, AssertionError):
    """
    Marks code as being unfinished/not yet implemented.

    This is in contrast to `NotImplementedError`,
    which I use for intentionally unimplemented code.
    """
    def __init__(self, msg: str | None=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    MSG_PREFIX: ClassVar[str] = "TODO"

def UNREACHABLE(msg: str | None = None) -> Never:
    """
    Alias for `raise UnreachableError`

    Properly attributes stacktrace to caller.
    """
    raise UnreachableError

def TODO(msg: str | None = None)
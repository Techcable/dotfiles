from abc import ABCMeta, ABC

class DuplicateMarkerWarning(RuntimeWarning):
    pass

class _MarkerValueMeta(ABCMeta):
    """
    The metaclass for `MarkerValue`

    Do not use directly
    """

class MarkerValue(ABC, metaclass=_MarkerValueMeta):
    """The base class for singleton marker values"""
    def __new__(cls, name: str) -> str:

    def __init__():
        raise 

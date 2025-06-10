from __future__ import annotations

import operator
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Iterator, overload

from . import PlatformPath

__all__ = ("PythonVersion", "PythonInterpreter")


class PythonVersion(tuple[int, ...]):
    @overload
    def __new__(cls, s: str, /) -> PythonVersion: ...

    @overload
    def __new__(cls, *args: int) -> PythonVersion: ...

    def __new__(cls, *args):
        match args:
            case [str(val)]:
                assert "." in val
                return tuple.__new__(cls, map(int, val.split(".")))
            case tuple(_):
                assert all(isinstance(val, int) for val in args)
                assert len(args) >= 2
                return tuple.__new__(cls, args)
            case _:
                raise TypeError(type(args))

    def __repr__(self) -> str:
        return f"PythonVersion({str(self)!r})"

    def __str__(self) -> str:
        return ".".join(map(str, self))

    @property
    def major_version(self) -> int:
        return self[0]


@dataclass(frozen=True)
class PythonInterpreter:
    brew_name: str
    version: PythonVersion
    home: Path

    def __post_init__(self):
        assert self.version[0] == 3, "Only python 3 is supported"
        assert self.brew_name.startswith(PythonInterpreter.HOMEBREW_NAME_PREFIX)
        if not self.binary.is_file():
            raise FileNotFoundError(f"Missing binary for {self}")

    @property
    def binary(self) -> Path:
        return self.home / "bin" / f"python{self.version}"

    @property
    def source(self) -> str:
        return "homebrew"

    def __str__(self):
        return f"{self.source} python{self.version} @ {self.home}"

    HOMEBREW_NAME_PREFIX: ClassVar[str] = "python@"

    @staticmethod
    def homebrew_interpreters() -> Iterator[PythonInterpreter]:
        """Detect (homebrew) python interpreters"""
        if sys.platform != "darwin":
            raise OSError(f"Not on macos! plaltform={sys.platform}")
        name_prefix = PythonInterpreter.HOMEBREW_NAME_PREFIX
        for python_home in (PlatformPath.HOMEBREW_PREFIX.resolve() / "opt").glob("python@3.*"):
            assert (python_home / "bin").is_dir()
            name = python_home.name
            assert name != name_prefix, "Should only return specifics!"
            assert name.startswith(name_prefix)
            ver = PythonVersion(name.removeprefix(name_prefix))
            yield PythonInterpreter(brew_name=python_home.name, version=ver, home=python_home)

    @staticmethod
    def latest_homebrew_interpreter() -> PythonInterpreter:
        """Return the latest homebrew interpreter"""
        # Throws IndexError if none are installed
        return sorted(
            PythonInterpreter.homebrew_interpreters(),
            key=operator.attrgetter("version"),
        )[-1]

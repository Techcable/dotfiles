from __future__ import annotations

import os
from abc import ABCMeta, abstractmethod
from dataclasses import KW_ONLY, dataclass
from pathlib import Path
from subprocess import PIPE, CalledProcessError, run
from typing import TYPE_CHECKING

from dotfiles.translate_shell.__main__ import ConfigException
from dotfiles.translate_shell.cache import Cache, CachedValue, RehashFilesChanged

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import ClassVar

    from dotfiles.translate_shell.__main__ import Mode

__all__ = ("AddSupportBins", "AppAction", "AppInfo")


@dataclass
class AppInfo:
    app_name: str
    _: KW_ONLY
    executable_name: str
    main_bin_path: Path | None
    support_bin_dir: Path | None
    _mode: Mode

    def _warning(self, msg: str):
        """
        Gives the specified warning, unless this app has already given a warning.

        Each app instance will give at most one warning.
        """
        self._mode.warning(msg)
        # Disable future warnings for this app
        self._warning = lambda _msg: None  # type: ignore[method-assign]

    def add_support_bins(self, *, expected_bins: Sequence[str]):
        """Add the support binaries to the $PATH variable"""
        if not self._check_main_bin():
            return
        if self.support_bin_dir is None:
            self._warning(f"Unable to detect support bin dir for {self.app_name}")
            return
        assert isinstance(self.support_bin_dir, Path)
        # loop over expected bins, warning if anything is missing
        #
        # break on first warning, to limit output
        # This limit is local to this loop & seperate from class limit
        for expected_bin in expected_bins:
            expected_loc = self.support_bin_dir / expected_bin
            if not expected_loc.is_file():
                self._mode.warning(
                    f"Missing expected support bin for {self.app_name}: {expected_bin!r}"
                )
                break  # limit to one warning per loop
            elif not os.access(expected_loc, os.X_OK):
                self._mode.warning(
                    f"Expected support bin to be executable: {str(expected_loc)!r}"
                )
                break  # limit to one warning per loop
        self._mode.extend_path(self.support_bin_dir)

    def _check_main_bin(self) -> Path | None:
        if self.main_bin_path is None:
            self._warning(
                f"Missing binary path for {self.app_name}: {self.main_bin_path!r}"
            )
        return self.main_bin_path

    def setup_alias(self):
        main_bin_path = self._check_main_bin()
        if main_bin_path is None:
            return
        self._mode.alias(
            self.executable_name.lower().replace("_", "-").replace(" ", "-"),
            self._mode.run_in_background_helper([str(self.main_bin_path)]),
            wraps=None,
        )

    if TYPE_CHECKING:

        @staticmethod
        def analyse(app_name: str, *, cache: Cache, mode: Mode) -> AppInfo | None:
            ...


def _analyse_app(app_name: str, *, cache: Cache, mode: Mode) -> AppInfo | None:
    app_root = Path(f"/Applications/{app_name}.app")
    if not app_root.is_dir():
        mode.warning(
            f"Unable to find application {app_name}: Missing directory {app_root!r}"
        )
        return None

    # NOTE: Invoking a subprocess here is super slow
    # We cache it to speed up startup.
    def load_executable_name() -> CachedValue[str]:
        info_file = app_root / "Contents/Info.plist"
        try:
            value = run(
                ["defaults", "read", str(info_file), "CFBundleExecutable"],
                check=True,
                stdout=PIPE,
                encoding="utf8",
            ).stdout.rstrip()
        except CalledProcessError:
            mode.warning(f"Unable to detect executable name for {app_root!r}")
            raise ConfigException
        return CachedValue(
            value=value, rehash=RehashFilesChanged.for_files([info_file])
        )

    executable_name: str = cache.get_or_load(
        f"executable_name[{app_name}]", load_executable_name
    )

    support_bin_dir: Path | None = app_root / "Contents/SharedSupport/bin"
    main_bin_path: Path | None = app_root / "Contents/MacOS" / executable_name
    assert support_bin_dir is not None and main_bin_path is not None  # satisfy mypy
    if not support_bin_dir.is_dir():
        support_bin_dir = None
    if not main_bin_path.is_file():
        main_bin_path = None

    return AppInfo(
        app_name,
        executable_name=executable_name,
        main_bin_path=main_bin_path,
        support_bin_dir=support_bin_dir,
        _mode=mode,
    )


if not TYPE_CHECKING:
    AppInfo.analyse = staticmethod(_analyse_app)


class AppAction(metaclass=ABCMeta):
    @abstractmethod
    def run(self, info: AppInfo):
        pass

    @staticmethod
    def simple(callback: Callable[[AppInfo], None]) -> AppAction:
        return _SimpleAppAction(callback)

    SETUP_ALIAS: ClassVar[AppAction]


@dataclass
class _SimpleAppAction(AppAction):
    callback: Callable[[AppInfo], None]

    def run(self, info: AppInfo):
        self.callback(info)


AppAction.SETUP_ALIAS = AppAction.simple(AppInfo.setup_alias)


@dataclass(kw_only=True)
class AddSupportBins(AppAction):
    expected_bins: Sequence[str]

    def run(self, info: AppInfo):
        info.add_support_bins(expected_bins=self.expected_bins)

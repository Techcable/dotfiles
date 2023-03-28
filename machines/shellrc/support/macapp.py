from __future__ import annotations

from pathlib import Path
from subprocess import PIPE, CalledProcessError, run
from typing import TYPE_CHECKING

from dotfiles.translate_shell.cache import Cache, CachedValue, RehashFilesChanged

if TYPE_CHECKING:
    from dotfiles.translate_shell.__main__ import Mode

__all__ = ("setup_app_alias",)


def setup_app_alias(app_name: str, *, mode: Mode, cache: Cache) -> None:
    app_root = Path(f"/Applications/{app_name}.app")
    if not app_root.is_dir():
        mode.warning(
            f"Unable to find application {app_name}: Missing directory {app_root!r}"
        )
        return

    # NOTE: Invoking a subprocess here is super slow
    # We cache it to speed up startup.
    def load_executable_name():
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

    executable_name = cache.get_or_load(
        f"executable_name[{app_name}]", load_executable_name
    )

    support_bin_dir = app_root / "Contents/SharedSupport/bin"
    main_bin_path = app_root / "Contents/MacOS" / executable_name
    if not main_bin_path.is_file():
        mode.warning(f"Missing binary path for {app_name}: {main_bin_path!r}")
    elif support_bin_dir.is_dir():
        mode.extend_path(support_bin_dir)
    else:
        mode.alias(
            executable_name.lower().replace("_", "-").replace(" ", "-"),
            mode.run_in_background_helper([str(main_bin_path)]),
        )

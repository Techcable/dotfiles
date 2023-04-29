# Configuration for my 2021 Macbook Pro
from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from techcable.pyinterp import PythonInterpreter

from dotfiles.translate_shell.cache import Cache

from .support.macapp import AddSupportBins, AppAction, AppInfo

if TYPE_CHECKING:
    from typing import Optional, Union

    from dotfiles.translate_shell.config_api import *

HOMEBREW_ROOT = Path("/opt/homebrew")

CACHE = Cache.open("macbook-config")

export("MACHINE_NAME", "macbook-2021")
export("MACHINE_NAME_SHORT", "macbook")

# Automatically uses the default browser
export("BROWSER", Path("/usr/bin/open"))

if not PLATFORM.is_desktop():
    warning("Expected a desktop environment for macbook!")

# Use homebrew sdk
preferred_java_home = Path("/Library/Java/JavaVirtualMachines/homebrew-openjdk")
if not (preferred_java_home / "Contents/Home").is_dir():
    warning("Unable to detect java version")
else:
    export("JAVA_HOME", preferred_java_home / "Contents/Home")

haxe_std_path = Path("/opt/homebrew/lib/haxe/std")
if haxe_std_path.is_dir():
    export("HAXE_STD_PATH", haxe_std_path)
else:
    warning(f"Expected haxe stdlib: {haxe_std_path}")


APPS: dict[str, AppAction] = {
    "Keybase": AddSupportBins(expected_bins=("keybase",)),
    "Sublime Merge": AddSupportBins(expected_bins=("smerge",)),
    "Sublime Text": AddSupportBins(expected_bins=("subl",)),
    "Texifier": AppAction.SETUP_ALIAS,
}
assert list(APPS.keys()) == sorted(APPS.keys()), "App keys should be sorted"

# TODO: Sublime Text and Keybase seem to already have added themselves
# to the path, making this code redundant.
#
# Sublime Text made a symlink from Sublime Text.app/.../subl => /usr/bin/subl
# Keybase added an entry to /etc/paths.d


def _analyse_all_apps():
    for app_name, actions in APPS.items():
        app_info = AppInfo.analyse(app_name, cache=CACHE, mode=_MODE_IMPL)
        if isinstance(actions, AppAction):
            action_list = [actions]
        else:
            raise TypeError
        for action in action_list:
            action.run(app_info)


_analyse_all_apps()
del _analyse_all_apps

# pipx
extend_path("~/.local/bin")  # path for pipx

# Override pipx default python
#
# Otherwise it will hardcode against a specific minor version like:
# /opt/homebrew/Cellar/python@3.11/3.11.2/Frameworks/Python.framework/Versions/3.11/bin/python3.11
#
# This will cause problems when minor version upgrades
export(
    "PIPX_DEFAULT_PYTHON", str(PythonInterpreter.latest_homebrew_interpreter().binary)
)

# $GOBIN (used for go install)
go_bin = Path.home() / "go/bin"
if go_bin.is_dir():
    extend_path(str(go_bin))
else:
    warning("Missing $GOBIN directory", str(go_bin))


# Scala installation managed by "coursier". See here: https://get-coursier.io/docs/cli-overview
extend_path("~/Library/Application Support/Coursier/bin")

# Custom $PKG_CONFIG_PATH (to find libraries)

# Homebrew pkg-config path must be explicitly put first, in order to override any future kegs
#
# This way we get homebrew python version instead of keg python version
#
# The default behavior is to have $PKG_CONFIG_PATH override the automatically
# detected libraires (including homebrew libraries).
extend_path("/opt/homebrew/lib/pkgconfig", "PKG_CONFIG_PATH")

# senpai IRC client (CLI): https://sr.ht/~taiite/senpai/
extend_path("/opt/senpai/bin")
extend_path("/opt/senpai/share/man", "MANPATH")

# MacGPG: https://gpgtools.org/
extend_path("/usr/local/MacGPG2/bin")
extend_path("/usr/local/MacGPG2/share/man", "MANPATH")


# Calling `brew list --versions janet` takes 500 ms,
# using `janet -v` takes 5ms
#
# However even faster to skip subprocess detection
# and rely on homebrew directory structure
def detect_janet_version() -> Optional[str]:
    try:
        janet_exe_path: Union[Path, str, None]
        if (janet_exe_path := which("janet")) is not None:
            janet_exe_path = Path(janet_exe_path).readlink()
        else:
            return None
    except OSError:
        return None

    m = re.fullmatch(r"../Cellar/janet/([^/]+)/bin/janet", str(janet_exe_path))
    if m is not None:
        return m.group(1)
    else:
        return None


current_janet_version = detect_janet_version()
if current_janet_version is None:
    warning(
        "Unable to detect Janet version based on PATH (is it installed into homebrew cellar?)"
    )
del detect_janet_version  # scoping ;)

if current_janet_version is not None:
    # add janet-specific bin path (used for janet binary packages)
    extend_path(f"/opt/homebrew/Cellar/janet/{current_janet_version}/bin")
else:
    warning("Missing janet version")

# Unversioned python provided by homebrew
#
# Resolves a strange conflict with a 'pip' command for wrong version
extend_path("/opt/homebrew/opt/python/libexec/bin")


# Some homebrew things are "keg-only" meaning they are not on the path by default
#
# Usually these are alternative versions of the main package.
# Particular examples are lua@5.3 and python@3.10
#
# We want these on the path, but we want them at the end (lower precedence)
# so they don't conflict with existing versions
#
# Use the extend_path builtin to add it to the end (but only if the keg exists)
def detect_keg(name: str, *, order: Optional[PathOrderSpec] = None):
    keg_prefix = Path("/opt/homebrew/opt")
    if (keg_bin := keg_prefix / f"{name}/bin").is_dir():
        # echo "Detected keg $1";
        extend_path(keg_bin, order=order)
    if (keg_pkgconfig := keg_prefix / f"{name}/lib/pkgconfig").is_dir():
        extend_path(keg_pkgconfig, "PKG_CONFIG_PATH", order=order)


detect_keg("lua@5.3")
# Detect LLVM keg. This is nessicary because homebrew llvm
# has some utilities that system LLVM does not have (like clang-format and )
#
# This is lower priority than system LLVM,
# so system clang will be prefered over homebrew clang.
# This only makes a difference for those
# specific tools that are missing in the system installation.
#
# This seems likely to cause issues with mismatches between homebrew LLVM/clang
# and system LLVM/clang. However, I need clang-format (which is only in Homebrew)
# and right now I still want to keep using the system clang,
# so we are stuck with this
detect_keg("llvm", order=PathOrderSpec.APPEND_SYSTEM)

# Mac has no LDD command
#
# See here: https://discussions.apple.com/thread/309193 for suggestion
# Also "Rosetta stone for Unixes"
alias("ldd", "echo 'Using otool -L' && otool -L", wraps="otool -L")

if which("pacaptr") is not None:
    # alias pacman=pacaptr
    alias("pacman", "pacaptr", wraps=ALIAS_WRAPS_UPDATED)

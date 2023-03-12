"""Default configuration shared across all machines"""
import os
import sys
from pathlib import Path
from subprocess import PIPE, run
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from translate.config_api import *

try:
    assert DOTFILES_PATH == Path(os.environ["DOTFILES_PATH"])
except KeyError:
    warning("Missing $DOTFILES_PATH environment variable")

# Rust binaries
#
# NOTE: This contains almost all the binaries in ~/.rustup/toolchain/<default toolchain>/bin
extend_path("~/.cargo/bin")
# My private bin ($HOME/bin)
extend_path("~/bin")

# add dotfiles scripts directory
#
# These are convenient scripts I want to sync across all
# my computers
extend_path(DOTFILES_PATH / "scripts")

# I like neovim
export("EDITOR", "nvim")

# See stackoverflow: https://stackoverflow.com/a/41054093
export("GPG_TTY", run(["tty"], stdout=PIPE, encoding="utf8").stdout.rstrip())

# Add jetbrains user_config
if PLATFORM.is_desktop():
    try:
        jetbrains_app_dir = (
            AppDir.USER_DATA.resolve(PLATFORM) / "JetBrains/Toolbox/scripts"
        )
        if jetbrains_app_dir.is_dir():
            extend_path(jetbrains_app_dir)
        else:
            raise FileNotFoundError(f"could not find directory {jetbrains_app_dir}")
    except (UnsupportedPlatformError, FileNotFoundError) as e:
        warning("While attempting to detect jetbrains script path, " + str(e))

# Have pip-run cache its created environments
#
# https://github.com/jaraco/pip-run#environment-persistence
#
# TODO: This may eventually result in bloat :/
# It is never cleaned up.
export("PIP_RUN_MODE", "persist")

# Extra aliases when running under kitty
#
# TODO: Is this redundant with kitty's new shell integration?
# https://sw.kovidgoyal.net/kitty/shell-integration/
if os.getenv("TERM") == "xterm-kitty":
    alias("icat", "kitty +kitten icat")
    alias("diff", "kitty +kitten diff")

    # Need to fix ssh for kitty
    alias("ssh", "kitty +kitten ssh")


# NOTE: The `which` command doesn't update with path :/
# which("betterstat"):

alias("stat", "betterstat")

# Prefer lsd to ls
#
# We used to use `exa`,
# but that is now second priority
if which("lsd"):
    alias("ls", "lsd")
    alias("lsa", "lsd -A")

    # Shortcuts for seeing sizes
    alias("lsds", "lsd -A --blocks size,name")
    alias("lsdl", "lsd -A --long")
elif which("exa"):
    warning("Missing lsd (but has `exa` installed)")
else:
    warning("Cannot find lsd or exa")

# Warn on usage of bpytop
if real_bpytop := which("bpytop"):
    if which("btop"):
        alias(
            "bpytop",
            f'{real_bpytop}; echo "{set_color("yellow", bold=True)}NOTE{reset_color()}: Please consider using btop"',
        )
    else:
        warning("bpytop is installed, but not btop")
else:
    warning("bpytop is not installed")

extend_python_path(DOTFILES_PATH / "libs/python")

if (
    legacy_config := Path("~/.shell-config.rc").expanduser()
).exists() or legacy_config.is_symlink():
    warning(
        f"Legacy config file should not exist: ~/{legacy_config.relative_to(Path.home())}"
    )

# This is xonsh-specific (not even sure why it's here)
#
# We Prefix with 'py' to indicate we are in xonsh
# We really should be prefixing with 'xonsh', but 'py' is shorter
# It's not really ambiguous, since this is really the python-prompt (for all
# intents and purposes)
# I'm not going to confuse with the regular python interpreter (python3) cause i'll
# know its a shell
#
# This is the default value for
export("XONSH_PREFIX", "py")
export("XONSH_PREFIX_COLOR", "yellow")

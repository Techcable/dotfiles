"""Default configuration shared across all machines"""
import os
import shutil
from pathlib import Path
from subprocess import PIPE, run

try:
    DOTFILES_PATH = Path(os.environ["DOTFILES_PATH"])
except KeyError:
    warning("Missing $DOTFILES_PATH environment variable")
    DOTFILES_PATH = Path.home()  # dummy


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

# Setup opam (ocaml) package manager if available
#
# TODO: This clobbers path
# Essentially it executes at comptime what should be done at runtime
if shutil.which("opam") and False:
    if SHELL_BACKEND == "xonsh":
        # Sadly, opam has no xonsh support directly
        #
        # We pass through zsh2xonsh instead
        try:
            import zsh2xonsh

            zsh_envinit = run(
                ["opam", "env", "--shell=zsh"], stdout=PIPE, encoding="utf8"
            ).stdout.rstrip()
            translated_envinit = zsh2xonsh.translate_to_xonsh(zsh_envinit)
            eval_text(translated_envinit)
        except ImportError:
            warning("Unable to import zsh2xonsh, cannot resolve opam")
    elif SHELL_BACKEND in ("zsh", "fish"):
        # Otherwise natively supported
        eval_text(
            run(
                ["opam", "env", f"--shell={SHELL_BACKEND}"],
                stdout=PIPE,
                encoding="utf8",
            ).stdout.rstrip()
        )
    else:
        raise AssertionError(SHELL_BACKEND)

# Fix GPG error "Inappropriate ioctl for device"
# See stackoverflow: https://stackoverflow.com/a/41054093
export("GPG_TTY", run(["tty"], stdout=PIPE, encoding="utf8").stdout.rstrip())

# Extra aliases when running under kitty
#
# TODO: Is this redundant with kitty's new shell integration?
# https://sw.kovidgoyal.net/kitty/shell-integration/
if os.getenv("TERM") == "xterm-kitty":
    alias("icat", "kitty +kitten icat")
    alias("diff", "kitty +kitten diff")

    # Need to fix ssh for kitty
    alias("ssh", "kitty +kitten ssh")


# Prefer exa to ls
if shutil.which("exa"):
    alias("ls", "exa")
    alias("lsa", "exa -a")

# Warn on usage of bpytop
if shutil.which("bpytop"):
    if shutil.which("btop"):
        alias(
            "bpytop",
            f'bpytop; echo "{set_color("yellow", bold=True)}NOTE{reset_color()}: Please consider using btop"',
        )
    else:
        warning("bpytop is installed, but not btop")
else:
    warning("bpytop is not installed")

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

# Configuration for my 2017 Arch Linux Lenovo Laptop
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from translate.config_api import *

if not PLATFORM.is_desktop():
    warning("Not on a desktop! (TODO: Refine check)")

export("MACHINE_NAME", "archlinux-lenovo-2017")
export("MACHINE_NAME_SHORT", "archtop")
export("MACHINE_PREFIX_COLOR", set_color("cyan", bold=True))
export("BROWSER", "/usr/bin/firefox")

extend_path("~/.yarn/bin")
extend_path("~/go/bin")

# Where pip puts its bin files
extend_path("~/.local/bin")
# TODO: I really don't like hardcoding these
extend_path("~/.gem/ruby/2.5.0/bin")
# TODO: Remove this and rely on ~/.cargo bin (See commit ee1052b64946896)
extend_path("~/.rustup/toolchains/nightly-x86_64-unknown-linux-gnu/bin/")

# NOTE: Prefix with 'py' to indicate we are in xonsh
# We really should be prefixing with 'xonsh', but 'py' is shorter
# It's not really ambiguous, since this is really the python-prompt (for all
# intents and purposes)
# I'm not going to confuse with the regular python interpreter (python3) cause i'll
# know its a shell
export("XONSH_PREFIX", "py")
export("XONSH_PREFIX_COLOR", "yellow")

# aurutils
export("AUR_DEST", Path.home() / "git/aur")
export("AUR_PAGER", "ranger")
# seems like a good idea....
export("AUR_CONFIRM_PAGER", "1")
# this is magic...
export("AUR_SYNC_USE_NINJA", "1")

# Configuration for my primary server for techcable.net
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dotfiles.translate_shell.config_api import *

export("MACHINE_NAME", "server-techcable")
export("MACHINE_NAME_SHORT", "server")
export("MACHINE_PREFIX_COLOR", set_color("red", bold=True))

# Apparently my PATH had no customizations in my old .zshrc


# NOTE: I don't use xonsh on the server,
# so we should never have to set XONSH_PREFIX
if SHELL_BACKEND == "xonsh":
    raise AssertionError("Xonsh shell not supported on server!")
    # export("XONSH_PREFIX", "py-server")

# aurutils
export("AUR_PAGER", "ranger")
# seems like a good idea....
export("AUR_CONFIRM_PAGER", "1")
# this is magic...
export("AUR_SYNC_USE_NINJA", "1")

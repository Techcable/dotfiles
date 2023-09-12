# Configuration for my primary server for techcable.net
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dotfiles.translate_shell.config_api import *

# NOTE: This was the configuration for the *LEGACY* server using Arch
# TODO: Make this indication clearer

set -gx MACHINE_NAME "server-techcable"
set -gx MACHINE_NAME_SHORT "server"
set -gx MACHINE_PREFIX_COLOR $(set_color --bold red)

# Apparently my PATH had no customizations in my old .zshrc

# aurutils
set -gx AUR_PAGER "ranger"
# seems like a good idea....
set -gx AUR_CONFIRM_PAGER 1
# this is magic...
set -gx AUR_SYNC_USE_NINJA 1
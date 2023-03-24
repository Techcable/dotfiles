# Configuration for my 2022 Raspberry Pi 4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dotfiles.translate_shell.config_api import *

export("MACHINE_NAME", "raspberrypi4-2022")

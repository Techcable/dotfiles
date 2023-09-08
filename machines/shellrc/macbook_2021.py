# Configuration for my 2021 Macbook Pro
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dotfiles.translate_shell.config_api import *

MACHINE_NAME = "macbook-2021"
MACHINE_NAME_SHORT = "macbook"

fish_config_file = DOTFILES_PATH / f"machines/shellrc/{MACHINE_NAME.replace('-', '_')}.fish"
if fish_config_file.is_file():
    source_file(fish_config_file)
else:
    print(f"ERROR: Unable to find fish config file for {MACHINE_NAME}!", file=sys.stderr)
    print(f"{' ' * 8}Expected it to exist at {fish_config_file}", file=sys.stderr)

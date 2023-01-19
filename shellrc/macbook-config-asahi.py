# Configuration for Asahi linux, running within my M1 macbook-2021
import os
from pathlib import Path

export("MACHINE_NAME", "macbook-2021-asahi")
export("MACHINE_NAME_SHORT", "apple" + set_color("cyan", bold=True) + "arch")
export("MACHINE_PREFIX_COLOR", set_color("green"))
export("BROWSER", "/usr/bin/firefox")

# NOTE: Prefix with 'py' to indicate we are in xonsh
# We really should be prefixing with 'xonsh', but 'py' is shorter
# It's not really ambiguous, since this is really the python-prompt (for all
# intents and purposes)
# I'm not going to confuse with the regular python interpreter (python3) cause i'll
# know its a shell
export("XONSH_PREFIX", "py")
export("XONSH_PREFIX_COLOR", "yellow")

export("SSH_AUTH_SOCK", Path(os.getenv("XDG_RUNTIME_DIR")) / "ssh-agent.socket")

# aurutils
export("AUR_PAGER", "ranger")
# seems like a good idea....
export("AUR_CONFIRM_PAGER", "1")
# this is magic...
export("AUR_SYNC_USE_NINJA", "1")

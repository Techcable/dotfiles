# Configuration for the Alpine Linux VM, running inside my 2021 Macbook Pro ^_^
from pathlib import Path

export("MACHINE_NAME", "alpine-vm-macbook-2021")

# On alpine, sudo -> doas
alias("sudo", "doas")

# Set default python to python3
alias("python", "python3")

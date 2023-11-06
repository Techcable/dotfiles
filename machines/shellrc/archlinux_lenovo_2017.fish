# Configuration for my 2017 Arch Linux Lenovo Laptop

set -gx MACHINE_NAME archlinux-lenovo-2017
set -gx MACHINE_NAME_SHORT archtop
set -gx MACHINE_PREFIX_COLOR $(set_color --bold "cyan")

set -gx BROWSER "/usr/bin/firefox"

fish_add_path --global "$HOME/.yarn/bin"
fish_add_path --global "$HOME/go/bin"

# Where pip puts its bin files
fish_add_path "$HOME/.local/bin"

# TODO: I really don't like hardcoding this
fish_add_path "$HOME/.gem/ruby/2.5.0/bin"

# TODO: Remove this and rely on ~/.cargo bin (See commit ee1052b64946896)
fish_add_path "$HOME/.rustup/toolchains/nightly-x86_64-unknown-linux-gnu/bin"

# aurutils
set -gx AUR_DEST "$HOME/git/aur"
set -gx AUR_PAGER "ranger"
# seems like a good idea....
set -gx AUR_CONFIRM_PAGER 1
# this is magic...
set -gx AUR_SYNC_USE_NINJA 1

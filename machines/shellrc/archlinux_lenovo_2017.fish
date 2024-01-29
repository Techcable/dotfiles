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

# On Arch, the boost package uses the `b2` command,
# so backblaze is stuck with backblaze-b2
#
# Give informative reminders about this (first time only)
function b2 -d='Override boost-b2, alias for backblaze-b2' --wraps="backblaze-b2"
    if not set --query _backblaze_b2_command_gave_warning
        set --local b2_cmd_package $(pacman -Qoq $(command --search b2))
        if test "$b2_cmd_package" = "boost"
            warning "This alias overrides `b2` command to be for backblaze (backblaze-b2). On arch, the default `b2` is for boost."
            echo "  $(set_color green)NOTE:$(set_color normal)  Use either `boost-b2` or `command b2` to access boost's b2 command." >&2
        else
            warning "The `b2` command is not for boost, but for $b2_package. Please update the shell config code."
        end
        set --global _backblaze_b2_command_gave_warning "yes"
    end
    command backblaze-b2 $argv
end

# Alias boost-b2 to the /usr/bin/b2 command,
# since b2 is now used for backblaze (see above)
alias boost-b2='command b2'

# aurutils
set -gx AUR_DEST "$HOME/git/aur"
set -gx AUR_PAGER "ranger"
# seems like a good idea....
set -gx AUR_CONFIRM_PAGER 1
# this is magic...
set -gx AUR_SYNC_USE_NINJA 1

# Configuration for Asahi linux, running within my M1 macbook-2021

set -gx MACHINE_NAME "macbook-2021-asahi"
set -gx MACHINE_NAME_SHORT "apple$(set_color --bold cyan)arch"
set -gx MACHINE_PREFIX_COLOR $(set_color green)

set -gx BROWSER "/usr/bin/firefox"

if test -d "$XDG_RUNTIME_DIR"
    set -gx SSH_AUTH_SOCK "$XDG_RUNTIME_DIR/ssh-agent.socket"
else
    warning "Unable to resolve $XDG_RUNTIME_DIR"
end

# aurutils
set -gx AUR_PAGER "ranger"
# seems like a good idea....
set -gx AUR_CONFIRM_PAGER 1
# this is magic...
set -gx AUR_SYNC_USE_NINJA 1

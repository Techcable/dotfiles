# NOTE: Must stay in sync with common.py


# NOTE: Intentionally skipped
# assert DOTFILES_PATH == Path(os.environ["DOTFILES_PATH"])

function warning
    echo "$(set_color --bold yellow)WARNING:$(set_color reset)" $argv >&2;
end

if not set -q DOTFILES_PATH
    warning "Variable not set: \$DOTFILES_PATH"
elif not test -d $DOTFILES_PATH
    warning "Unable to find dotfiles directory: `$DOTFILES_PATH`"
end

# Detect if desktop
if not string match --quiet "server" $MACHINE_NAME
    set --global MACHINE_DESKTOP 1
end

# Detect platform (equivalent to python sys.platform)
#
# Faster than uname due to caching
if string match --ignore-case --quiet -- "Darwin" $(uname)
    set --global MACHINE_PLATFORM "darwin"
else
    # If not MacOS, assume linux
    set --global MACHINE_PLATFORM "linux"

    begin
        # Detect distro via lsb_release
        set --local supported_distros "Arch"
        # Using string match on the file directly is orders
        # of magnitude faster than invoking lsb_release
        set --local detected_distro $(string match -rg 'DISTRIB_ID="?([^"]+)"?' < /etc/lsb-release)
        if not contains $detected_distro $supported_distros
            set detected_distro $(lsb_release --id --short)
            if test $status -ne 0
                warning "Failed to detect distro with `lsb_release`"
                set detected_distro "unknown"
            else if not contains $detected_distro $supported_distro
                warning "Unsupported distro: $detected_distro"
            end
        end
        set --global MACHINE_DISTRO $(string lower $detected_distro)

    end

end

# Rust binaries
#
# NOTE: This contains almost all the binaries in ~/.rustup/toolchain/<default toolchain>/bin
fish_add_path --global --append ~/.cargo/bin
# My private bin ($HOME/bin)
fish_add_path --global ~/bin

# add dotfiles scripts directory
#
# These are convenient scripts I want to sync across all
# my computers
fish_add_path --global --append "$DOTFILES_PATH/scripts"

# I like neovim
set -gx EDITOR nvim

# Prefer ov pager
begin
    set --local moar_url "https://github.com/walles/moar"
    set --local ov_url "https://noborus.github.io/ov/"
    if command -q ov
        # NOTE: Use `ov-less`, to get less-compatible keybindings
        if command -q ov-less
            # As of this writing, the ov-less command is not included in the AUR pacakge for `ov`.
            # To work around this, we write a small wrapper function to emulate it.
            #
            # However, if we find an ov-less on a system with pacman,
            # we question the need for the wrapper function.
            #
            # TODO: Just use the nix package and avoid this nonsense.
            if command -q pacman
                warning "Found ov-less command on system with pacman. Still need wrapper function to emulate it?"
            end
            set -gx PAGER "ov-less"
        else if command -q pacman; and pacman -Qq ov >/dev/null 2>&1
            # On archlinux (i.e. a distro with pacman), search for an ov-less config
            #
            # Then, use it to emulate an ov-less command.
            set --local ov_less_config $(pacman -Ql ov | string match -gr 'ov (.*/ov-less.yaml)$')
            if test -f "$ov_less_config"
                # Use the config file to emulate ov-less (present on mac & nix package, not in Arch)
                function ov-less --inherit-variable ov_less_config --wraps "ov" \
                    --description "The ov pager, conigured with less keybindings"
                    command ov --config $ov_less_config $argv
                end
                set -gx PAGER "ov --config $ov_less_config"
            else
                warning "Unable to find ov-less.yaml config for `ov` package. Using regular `ov` command for pager"
                set -gx PAGER "ov"
            end
        else
            warning "Unable to find `ov-less` command. Using regular `ov` command for pager"
            set -gx PAGER "ov"
        end
    else
        warning "Unable to find `ov` pager command (GitHub: $ov_url)"
    end
end

# See stackoverflow: https://stackoverflow.com/a/41054093
set -gx GPG_TTY "$(tty)"

# Add jetbrains user_config (if platform is not a desktop)
if set --query MACHINE_DESKTOP
    set --local user_data
    if test $MACHINE_PLATFORM = "darwin"
        set user_data "$HOME/Library/Application Support"
    else
        set user_data "$HOME/.local/share"
    end
    set --local jetbrains_app_dir "$user_data/JetBrains/Toolbox/scripts"
    if test -d "$jetbrains_app_dir"
        fish_add_path --global --append $jetbrains_app_dir
    else
        warning "could not find jetbrains script directory `$jetbrains_app_dir`"
    end
end

# Have pip-run cache its created environments
#
# https://github.com/jaraco/pip-run#environment-persistence
#
# TODO: This may eventually result in bloat :/
# It is never cleaned up.
set --global --export "PIP_RUN_MODE" "persist"

# Extra aliases when running under kitty
#
# TODO: Is this redundant with kitty's new shell integration?
# https://sw.kovidgoyal.net/kitty/shell-integration/
if test "$TERM" = "xterm-kitty"
    alias icat="kitty +kitten icat"
    alias diff="kitty +kitten diff"

    # Need to fix ssh for kitty
    #
    # NOTE: Do *not* use kitty for regular ssh
    #
    alias "kitty-ssh"="kitty +kitten ssh"
end

# Alias ranger -> r for easier access
if command --query "ranger"
    alias r="ranger"
else
    warning "The 'ranger' file manager is not installed"
end

if command --query betterstat
    alias stat=betterstat
else
    warning "Missing `betterstat` command"
end

# On desktop machines, setup 1Password for secrets
if set --query MACHINE_DESKTOP
    if not command --query op
        warning "Missing 1Password CLI on desktop ($MACHINE_NAME)"
    else
        # Use 1Password to store rclone config passwords
        #
        # Currently in bitwarden as well
        set -gx RCLONE_PASSWORD_COMMAND "op read \"op://Robot/rclone-config $MACHINE_NAME/password\""
    end
end

# Prefer lsd to ls
#
# We used to use `exa`,
# but that is now second priority
if command --query "lsd"
    alias ls="lsd"
    alias lsa="lsd -A"

    # Shortcuts for seeing sizes
    alias "lsds"="lsd -A --blocks size,name"
    alias "lsdl"="lsd -A --long"

    # Override tree command with `lsd --tree` (more consistent)
    alias "tree"="lsd --tree"
else if command --query "exa"
    warning "Missing lsd (but has `exa` installed)"
else
    warning "Cannot find lsd or exa"
end

# Warn on usage of bpytop
if command --query "bpytop"
    set --local real_bpytop $(command --search "bpytop")
    if command --query "btop"
        function bpytop --wraps bpytop --inherit-variable real_bpytop
            echo "$(set_color --bold yellow)NOTE:$(set_color reset) Please consider using btop"
            command $real_bpytop
        end
    else
        warning "bpytop is installed, but not btop"
    end
else
    warning "bpytop is not installed"
end

begin
    set --local dotfiles_python_libs "$DOTFILES_PATH/libs/python"
    if not test -d "$dotfiles_python_libs"
        warning "Missing dotfiles python libs: $dotfiles_python_libs"
    else if not contains $dotfiles_python_libs $PYTHONPATH
        set --global --append PYTHONPATH $dotfiles_python_libs
    end
end

begin
    set --local legacy_config "$HOME/.shell-config.rc"
    if test -e "$legacy_config"
        warning "Legacy config file should not exist: $legacy_config"
    end
end


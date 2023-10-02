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

# Prefer moar pager
begin
    set --local moar_url "https://github.com/walles/moar"
    if command -q moar
        set -gx PAGER "moar"
    else
        warning "Unable to find `moar` pager (GitHub: $moar_url)"
    end
end

# See stackoverflow: https://stackoverflow.com/a/41054093
set -gx GPG_TTY "$(tty)"

# Add jetbrains user_config (if platform is not a desktop)
if not string match --quiet "server" $MACHINE_NAME
    set --local user_data
    if string match --ignore-case --quiet -- "Darwin" $(uname)
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


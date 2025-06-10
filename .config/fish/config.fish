# Fish is my primary shell for interactive use
#
# I have stopped using xonsh pretty much at all,
# and only use zsh on my RamNode server.

function debug
    return; # Skip debug
    set_color --bold green
    echo -n "DEBUG: "
    set_color normal
    echo $argv
end

function warning
    set_color --bold yellow
    echo -n "WARNING: "
    set_color normal
    echo $argv
end

# Removed: Setup macports

# Setup homebrew
#
# This must come early because everything else depends on it
# Unfortunately `uname` is very slow (~29ms).
# Match on `status buildinfo` which is vastly faster
if status buildinfo | string match -q '*darwin'
    # avoid `brew shellenv` because it is slow (~30ms)
    # Instead, I do all the same things manually
    #
    # NOTE: Implicitly assumes using M1 mac
    set -gx HOMEBREW_PREFIX "/opt/homebrew"
    if test -d "$HOMEBREW_PREFIX";
        set -gx HOMEBREW_CELLAR "$HOMEBREW_PREFIX/Cellar"
        set -gx HOMEBREW_REPOSITORY "$HOMEBREW_PREFIX"
        fish_add_path --global --move --path "$HOMEBREW_PREFIX/bin" "$HOMEBREW_PREFIX/sbin";
        set --local homebrew_man_path "$HOMEBREW_PREFIX/share/man"
        if not contains $homebrew_man_path $MANPATH
            set -gx --append MANPATH $homebrew_man_path
        end
    else
        warning "Homebrew not installed in expected location: $HOMEBREW_PREFIX"
    end

end

# The set of missing dependencies that have alraedy been warned about
set -g missing_required_commands

function require_command
    # require_command [--repeat-warning] <cmd_name>
    #
    # Require the specified command <cmd_name> is present,
    # giving an error message if not.
    #
    # Unless --repeat-warning is specified, this will
    # only error the first time
    #
    # Returns 0 (true) if the command is present,
    # an error code (false) otherwise
    argparse --min-args 1 --max-args 1 'repeat-warning' -- $argv;
    set -f cmd_name $argv[1]
    if contains $cmd_name $missing_required_commands;
        set -f already_missing
        if not set -q _flag_repeat_warning
            return 1;
        end
    end
    if not which taplo >/dev/null 2>/dev/null
        warning "Missing required commands: $(set_color --bold brwhite){$cmd_name}$(set_color normal) (can install with cargo)"
        if not set -q already_missing
            set --append missing_required_commands $cmd_name
	end
        return 1;  # error
    end
end


set -gx DOTFILES_PATH $HOME/git/dotfiles

if not test -d "$DOTFILES_PATH"
   warning "Unable to load configuration (missing dotfiles)"
else
    set --local bootstrap_config_file ~/.dotfiles/bootstrap-config.toml
    set --local bootstrap_machine_name
    if not test -f "$bootstrap_config_file"
        warning "Unable to find dotfiles bootstrap config: $(string replace $HOME '~' $bootstrap_config_file)"
    else
        set bootstrap_machine_name $(taplo get --file-path $bootstrap_config_file .bootstrap.machine-name)
        if test \( $pipestatus[1] -ne 0 \) -o \( -z "$(string trim $bootstrap_machine_name)" \);
            warning "Unable to read \$MACHINE_NAME from the boostrap config"
            set --erase bootstrap_machine_name
        else
            # Set until machine-specific config does otherwise
            set -gx MACHINE_NAME $bootstrap_machine_name
        end
    end
    set --local shellrc_dir "$DOTFILES_PATH/machines/shellrc"
    set --local common_config_file "$shellrc_dir/common.fish"
    if test -f $common_config_file
        source $common_config_file
        or warning "Failed to evaluate common config: $common_config_file"
    else
        warning "Unable to find common config: `$common_config`"
    end
    # Run machine-specific config
    if set --query bootstrap_machine_name
        set --local machine_shellrc_name "$(string replace --all '-' '_' -- $MACHINE_NAME)"
        set --local machine_shellrc_file "$shellrc_dir/$machine_shellrc_name.fish"
        if test -f $machine_shellrc_file
            source $machine_shellrc_file;
            or warning "Failed to evaluate shellrc for $MACHINE_NAME: $machine_shellrc_file"
        else
            warning "Unable to find config for $machine_shellrc_name"
        end
        if test "$MACHINE_NAME" != "$bootstrap_machine_name"
            warning "Machine name set by machine shellrc ($MACHINE_NAME) " \
                "doesn't match bootstrap name ($bootstrap_machine_name)"
        end
    end
end

begin
    # Add dotfile completions
    set -l completion_root "$DOTFILES_PATH/completions"

    # NOTE: Order matters here
    for dir in $completion_root/{,$MACHINE_NAME};
        if not test -d $dir; mkdir -p $dir; end
        set -a fish_complete_path $dir;
    end
end

# Default to vim keybindings
set -g fish_key_bindings fish_vi_key_bindings

if status is-interactive
    # Commands to run in interactive sessions can go here


    # Search only for prefix, not whole word
    #
    # Thanks to @faho for pointing this out on Gitter
    bind \e\[A history-prefix-search-backward
    bind \e\[B history-prefix-search-forward

    if set -q KITTY_INSTALLATION_DIR
        set --global KITTY_SHELL_INTEGRATION enabled
        source "$KITTY_INSTALLATION_DIR/shell-integration/fish/vendor_conf.d/kitty-shell-integration.fish"
        set --prepend fish_complete_path "$KITTY_INSTALLATION_DIR/shell-integration/fish/vendor_completions.d"
    end

    # Shorter name for 'math' builtin
    alias m math
end

# Setup locale info for biff <https://github.com/BurntSushi/biff>
# Appears to be able to detect the timezone on its own
set -gx BIFF_LOCALE en-US


# Do not initialize `conda` - takes ~172 ms
# /Users/nicholas/lib/mambaforge/bin/conda "shell.fish" "hook" $argv | source

# Initialize bookmark-cd, alias as `b`
if command -q bookmark-cd
    bookmark-cd init | source
    alias b=bcd
end

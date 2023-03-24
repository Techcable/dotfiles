# NOTE: I really like this fish thing.
#
# I should look into it in case xonsh falls flat :)

function warning
    set_color --bold yellow
    echo -n "WARNING: "
    set_color normal
    echo $argv
end

# Setup macports
#
# We want our PATH to be after homebrew (lower priority),
# so we need to add it first
if test (uname) = "Darwin"
    set -gx MACPORTS_PREFIX "/opt/local"
    if not test -d "$MACPORTS_PREFIX";
        warning "Failed to find macports prefix ($MACPORTS_PREFIX)"
        set --erase MACPORTS_PREFIX
    end
    # See also: /opt/local/share/macports/setupenv.bash
    fish_add_path --prepend --global --path PATH  "$MACPORTS_PREFIX/"{bin,sbin}
    set --path -p MANPATH "$share/man"
    # Disabled $DISPLAY because I want to avoid xorg

    #if test -z "$DISPLAY";
    #    export DISPLAY=":0.0"
    #end
end

# Setup homebrew
#
# This must come early because everything else depends on it
if test (uname) = "Darwin"
    eval (/opt/homebrew/bin/brew shellenv)
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

function setup_extra_config
    if ! test -d $DOTFILES_PATH
        warning "Unable to load configuration (missing dotfiles)"
        return 1;
    end
    require_command "taplo"; or return;
    set DOTFILES_BOOTSTRAP_CONFIG ~/.dotfiles/bootstrap-config.toml
    if not test -f $DOTFILES_BOOTSTRAP_CONFIG
        warning "Unable to find dotfiles bootstrap config: $(string replace $HOME '~' $DOTFILES_BOOTSTRAP_CONFIG)"
        return 1;
    end
    begin
        set -l machine_name $(taplo get --file-path $DOTFILES_BOOTSTRAP_CONFIG .bootstrap.machine-name)
        if test \( $pipestatus[1] -ne 0 \) -o \( -z "$(string trim $machine_name)" \); then
            warning "Unable to read \$MACHINE_NAME from the boostrap config"
            return 1;
        end
        set --global --export MACHINE_NAME $machine_name
    end
    set -f shellrc_files "$DOTFILES_PATH/machines/shellrc/common.py" "$DOTFILES_PATH/machines/shellrc/$(string replace --all '-' '_' -- $MACHINE_NAME).py"
    set -f translated_config_dir (mktemp -d -t dotfiles)
    set -f translate_args --mode fish
    for rcfile in $shellrc_files
        if ! test -f $rcfile
            warning "Missing required config file: $rcfile"
            return 1
        end
        set -f --append translated_config_files "$translated_config_dir/$(basename $rcfile)"
        set -f --append translate_args --in $rcfile --out $translated_config_files[-1]
    end
    python3 "$DOTFILES_PATH/shellrc/translate/translate_shell_config.py" $translate_args;
    if test $status -ne 0;
        warning "Failed to translate configs: $translated_config_files";
        echo "Debug vars:">&2;
        echo "  \$translate_args: `$(string replace --all $translated_config_dir "\$translated_config_dir" -- $(string join ' ' -- $translate_args))`">&2;
        echo "  \$translated_config_dir: $translated_config_dir"
        return 1;
    end
    for translated in $translated_config_files
        source $translated
    end
end
setup_extra_config
functions --erase setup_extra_config

begin
    # Add dotfile completions
    set -l completion_root "$DOTFILES_PATH/completions"

    # NOTE: Order matters here
    for dir in $completion_root/{,$MACHINE_NAME};
        if not test -d $dir; mkdir -p $dir; end
        set -a fish_complete_path $dir;
    end
end

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

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
if test -f /Users/nicholas/lib/mambaforge/bin/conda
    eval /Users/nicholas/lib/mambaforge/bin/conda "shell.fish" "hook" $argv | source
end

if test -f "/Users/nicholas/lib/mambaforge/etc/fish/conf.d/mamba.fish"
    source "/Users/nicholas/lib/mambaforge/etc/fish/conf.d/mamba.fish"
end
# <<< conda initialize <<<


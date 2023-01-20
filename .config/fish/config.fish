# NOTE: I really like this fish thing.
#
# I should look into it in case xonsh falls flat :)

# Setup homebrew
#
# This must come early because everything else depends on it
if test (uname) = "Darwin"
    eval (/opt/homebrew/bin/brew shellenv)
end

function warning
    set_color --bold yellow
    echo -n "WARNING: "
    set_color normal
    echo $argv
end

set -gx DOTFILES_PATH $HOME/git/dotfiles

function setup_extra_config
    if ! test -d $DOTFILES_PATH
        warning "Unable to load configuration (missing dotfiles)"
    end
    set -f config_files ~/.shell-config.rc "$DOTFILES_PATH/shellrc/common-config.py"
    set -f translated_config_dir (mktemp -d -t dotfiles)
    set -f translate_args --mode fish
    for config_file in $config_files
        if ! test -f $config_file
            warning "Missing required config file: $config_file"
            return 1
        end
        set -f --append translated_config_files "$translated_config_dir/$(basename $config_file)"
        set -f --append translate_args --in $config_file --out $translated_config_files[-1]
    end
    python3 "$DOTFILES_PATH/shellrc/translate/translate_shell_config.py" $translate_args;
    if test $status -ne 0;
        warning "Failed to translate configs: $translated_config_files";
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

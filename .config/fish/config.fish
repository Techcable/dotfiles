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

    set -l marker_file "$DOTFILES_PATH/.should-profile.txt"
    if test -f $marker_file
        set -f profile_type $(cat $marker_file)
        switch $profile_type
            case 'xctrace'
                echo "Using `xtrace` for profiling`
            case '*'
                set_color --bold red
                echo -n "ERROR: "
                set_color normal
                echo "Unexpected profile type: $marker_type
                set --erase profile_type
        end
        if set -q profile_type
            rm $marker_file;
        end
    end
    set -l config_files ~/.shell-config.rc "$DOTFILES_PATH/shellrc/common-config.py"
    set -f translate_out_dir $(mktemp -d -t dotfiles)
    for config_file in $config_files
        if ! test -f $config_file
            warning "Missing required config file: $config_file"
            return 1
        end
        # TODO: What if translation fails?
        set -l translate_proc_args "$DOTFILES_PATH/shellrc/translate/translate_shell_config.py" fish "$config_file"
        set -l translate_out_file "$translate_out_dir/$(basename config_file)"

        function simple_translate
            python3 $translate_proc_args > $translate_out_file;
        end


        if set --query should_profile
            warning "Profiling translation of $(basename $config_file)";
            pushd $DOTFILES_PATH/profiles;
            xctrace record --template "CPU Profiler"  --launch --target-stdout $translate_out_file -- \
                $(realpath ~/lib/python3.10/bin/python3) $translate_proc_args
            popd
        end
        match $should_profile
            case 'xctrace':
                pushd $DOTFILES_PATH/profiles;
                xctrace record --template "CPU Profiler"  --launch --target-stdout $translate_out_file -- \
                    $(realpath ~/lib/python3.10/bin/python3) $translate_proc_args
                popd
            case '*':
                warning "Unknown profiling type: $should_profile/$should_profile)
        end
        source $translate_out_file
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

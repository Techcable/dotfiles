# NOTE: I really like this fish thing.
#
# I should look into it in case xonsh falls flat :)

# Setup homebrew
#
# This must come early because everything else depends on it
eval (/opt/homebrew/bin/brew shellenv)

function warning
    set_color --bold yellow
    echo -n "WARNING: "
    set_color normal
    echo $argv
end

# TODO: Is this ever used?
set machine_name (rg 'export\(.*MACHINE_NAME' ~/.shell-config.py | env LUA_INIT="export = function(a, b) print(b) end" lua)

if test $machine_name = ""
   warning "Empty machine name"
end

set -gx DOTFILES_PATH $HOME/git/dotfiles

function setup_extra_config
    if ! test -d $DOTFILES_PATH
        warning "Unable to load configuration (missing dotfiles)"
    end
    set -l config_files ~/.shell-config.py "$DOTFILES_PATH/common-config.py"
    for config_file in $config_files
        if ! test -f $config_file
            warning "Missing required config file: $config_file"
            return 1
        end
        # TODO: What if translation fails?
        python3 "$DOTFILES_PATH/translate_shell_config.py" fish "$config_file" | source
    end
end
setup_extra_config
functions --erase setup_extra_config

# Add my custom completions
#
# NOTE: This must come BEFORE oh-my-zsh (which handles most completions)
set completion_root (dirname (readlink ~/.zshrc))/completion
set techcable_completions "$completion_root/fish"
set techcable_machine_completions "$completion_root/$machine_name/fish"
if test -d $techcable_completions
    set fish_complete_path $fish_complete_path $techcable_completions
else
    echo "WARNING: unable to find dotfiles 'completion/fish' directory"
end

if test -d "$techcable_machine_completions"
    set fish_complete_path $fish_complete_path $techcable_machine_completions
end

if status is-interactive
    # Commands to run in interactive sessions can go here


    # Search only for prefix, not whole word
    #
    # Thanks to @faho for pointing this out on Gitter 
    bind \e\[A history-prefix-search-backward
    bind \e\[B history-prefix-search-forward
end

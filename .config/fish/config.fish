# NOTE: I really like this fish thing.
#
# I should look into it in case xonsh falls flat :)

# Setup homebrew
#
# This must come early because everything else depends on it
eval (/opt/homebrew/bin/brew shellenv)

# TODO: Is this ever used?
set machine_name (rg 'export\(.*MACHINE_NAME' ~/.shell-config.py | env LUA_INIT="export = function(a, b) print(b) end" lua)

if test $machine_name = ""
   echo "WARNING: Empty machine name"
end

# TODO: Warning messages on failure?
python3 ~/git/dotfiles/translate_shell_config.py fish ~/.shell-config.py | source

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
end

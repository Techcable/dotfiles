# NOTE: I really like this fish thing.
#
# I should look into it in case xonsh falls flat :)

set machine_name (cat ~/.config.zsh | grep 'export MACHINE_NAME' | sed -E 's/export MACHINE_NAME="(.*)"/\1/')

if test $machine_name = ""
   echo "WARNING: Empty machine name"
end

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

set machine_name (cat ~/.config.zsh | grep 'export MACHINE_NAME' | sed -E 's/export MACHINE_NAME="(.*)"/\1/')

if status is-interactive
    # Commands to run in interactive sessions can go here
end

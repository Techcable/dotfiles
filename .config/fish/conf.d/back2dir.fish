# Return to the most recently used directory when starting fish shell
#
# Ported from this xontrib: https://github.com/anki-code/xontrib-back2dir
#
# Uses fish "universal variables" for storage
#
# TODO: Is using universal variables (as opposed to a dedicated file)
# going to slow things down or hurt SSD?

# Right before the first pompt is shown, we go back to the last directory
#
# As far as I can tell fish has no equivalent to @events.on_post_init
function __back2dir_on_init --on-event fish_prompt
    if test "$PWD" = "$HOME" -a -n "$techcable_back2dir_last_dir"
        if test -d $techcable_back2dir_last_dir
            cd $techcable_back2dir_last_dir
        else
            echo (set_color --bold yellow)WARNING(set_color brblack)\[back2dir\](set_color normal): Previous directory (set_color -u white)$techcable_back2dir_last_dir$(set_color normal) does not exist
            # Reset last path to home to avoid warning?
            set -U techcable_back2dir_last_dir $HOME
        end
    end
    # unload this function
    functions -e __back2dir_on_init
end

function __back2dir_on_chdir --on-variable PWD
    # Update last_dir
    set -U techcable_back2dir_last_dir $PWD
end

# Disable direnv by default, as it can take a long time to evaluate
set -gx DIRENV_DISABLE 1

# Function to enable direnv
function direnv-enable
    if set -q DIRENV_DISABLE
        set -f was_disabled 1
    else
        set -f was_disabled 0
    end
    if not set -g _DIRENV_HOOK_INIT
        set --erase DIRENV_DISABLE
        direnv hook fish | source
        set -g _DIRENV_HOOK_INIT 1
    else if test $was_disabled -ne 0
        set --erase DIRENV_DISABLE
        # Avoid direnv reload where possible, as it invalidates the nix cache
        direnv reload
    end
    direnv export fish | source
    # Update shell to indicate direnv is enabled
    set -gx SHELL_PROMPT_SUFFIX "($(set_color red)direnv$(set_color normal)) "
end



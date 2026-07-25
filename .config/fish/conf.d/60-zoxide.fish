begin
    # option to print path name before changing to it
    set -lx _ZO_ECHO 1
    zoxide init fish | source
end

# By default, zoxide's fish completion only offers plain `cd`-style path
# completion for `z`'s first argument, ignoring its frecency database.
# Override it to show zoxide's own ranked matches once a keyword is typed,
# still falling back to normal path completion when there's no keyword yet.
function __zoxide_z_complete
    set -l keywords (builtin commandline --current-process --tokenize)[2..-1]
    if test (builtin count $keywords) -eq 0
        complete --do-complete "'' "(builtin commandline --cut-at-cursor --current-token) | string match --regex -- '.*/$'
    else
        zoxide query --list --exclude (__zoxide_pwd) -- $keywords 2>/dev/null
    end
end

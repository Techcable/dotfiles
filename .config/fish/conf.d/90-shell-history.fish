# ShellHistory is only usable on macOS. Consider https://atuin.sh instead
# We avoid uname for speed reasons
if not status buildinfo | string match -q '*darwin';
    return
end

# ShellHistory records every command you run. Keep these lines at the end of the file.
if status is-interactive; and not set -q __shhist_loaded
    set -g __shhist_loaded 1
    fish_add_path --global --append "/Applications/ShellHistory.app/Contents/Helpers"
    # One session per shell, also for tmux panes and nested shells that share TERM_SESSION_ID.
    if set -q TERM_SESSION_ID
        set -gx SHHIST_SESSION "$TERM_SESSION_ID-$fish_pid-"(date +%s)
    else
        set -gx SHHIST_SESSION "$fish_pid-"(date +%s)
    end
    set -g __shhist_number 0

    function __shhist_preexec --on-event fish_preexec
        set -g __shhist_pwd "$PWD"
    end

    function __shhist_postexec --on-event fish_postexec
        set -l __shhist_exit $status
        set -l __shhist_command $argv[1]
        # Blank lines are not commands; fish keeps a command that starts with a space out of
        # history, and so does ShellHistory.
        if not string match -qr '\S' -- "$__shhist_command"; or string match -q -- ' *' "$__shhist_command"
            return
        end
        set -g __shhist_number (math $__shhist_number + 1)
        set -l __shhist_args record --shell fish --session "$SHHIST_SESSION" --number $__shhist_number --duration-ms $CMD_DURATION --exit-code $__shhist_exit --pwd "$__shhist_pwd" --to-pwd "$PWD" --username "$USER" --hostname "$hostname"
        if fish_is_root_user; and set -q SUDO_USER
            # A root shell started with sudo records into the history of the user who ran sudo.
            printf '%s' "$__shhist_command" | sudo --preserve-env --user "$SUDO_USER" "/Applications/ShellHistory.app/Contents/Helpers/shhist" $__shhist_args >/dev/null 2>&1 &
        else
            printf '%s' "$__shhist_command" | "/Applications/ShellHistory.app/Contents/Helpers/shhist" $__shhist_args >/dev/null 2>&1 &
        end
        disown 2>/dev/null
    end
end

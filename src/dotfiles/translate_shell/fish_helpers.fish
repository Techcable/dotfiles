function error
    echo "$(set_color red)ERROR:$(set_color reset)" $argv >&2
    return 1
end

function warning
    echo "$(set_color --bold yellow)WARNING:$(set_color reset)" $argv >&2;
end

function add_path_any
    argparse -x 'append,prepend,append-system' 'v/variable=' 'append-system' 'a/append' 'p/prepend' -- $argv
    or return
    set -l extra_flags
    if test $_flag_append_system
        # append directly to path (not $user_paths)
        # this means lower priority than system stuff 
        set -a extra_flags "-a" "--path"
    else if test $_flag_append
        set -a extra_flags "-a"
    else if test $_flag_prepend
        set -a extra_flags "-p"
    end
    if test (count $argv) -lt 1
        error "Insufficient arguments! Please specify path too add"
    else if test (count $argv) -gt 1
        error "Unexpected argument: $argv[2]"
    else
        set -f target_path $argv[1]
    end

    # Determine variable name to set (default to path)
    if set -q _flag_variable
        set -f var_name $_flag_variable
    else
        set -f var_name "PATH"
    end
    if not string match --quiet --entire "PATH" $var_name then
        warning "Variable name should contain `PATH`: $var_name"
    end

    if not test -d $target_path
        warning "Path does not exist: $target_path"
    else if test $var_name = "PATH"
        # Delegate to builtin
        fish_add_path -g $extra_flags $target_path
    else if contains $target_path $$var_name
        # What we want to add ($target_path) is already part of $$var_name,
        # therefore skip over it
    else
        # Not present yet, append
        set -gxa $var_name $target_path
    end
end

function clear_helper_funcs --description "Clear all the helper functions (except this one)"
    set -e error
    set -e warning
    set -e add_path_any
end

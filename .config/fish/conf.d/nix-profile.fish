if test -d ~/.nix-profile/bin
    # Fedora does not set MANPATH by default, so we initialize it using the manpath command
    if not set -q MANPATH;
        set -gx MANPATH $(manpath)
    end

    fish_add_path -g ~/.nix-profile/bin
    function _maybe_add_path
        set target_var $argv[1]
        set target $argv[2]
        if test -e $target; and not contains -- $target $$target_var
            set -gxa $target_var $target
        end
    end
    _maybe_add_path MANPATH ~/.nix-profile/share/man
    _maybe_add_path fish_complete_path ~/.nix-profile/share/fish/vendor_completions.d
    # TODO: Consider adding ~/.nix-profile/share/fish/vendor_conf.d to init path.
    # This would end up running the direnv init hook and it
    # looks like might have to source it directly rather than adjusting the path var

    # done with the helper function
    functions --erase _maybe_add_path
end

# Setup homebrew
#
# This must come early because everything else depends on it
# Unfortunately `uname` is very slow (~29ms).
# Match on `status buildinfo` which is vastly faster
if status buildinfo | string match -q '*darwin'
    # avoid `brew shellenv` because it is slow (~30ms)
    # Instead, I do all the same things manually
    #
    # NOTE: Implicitly assumes using M1 mac
    set -gx HOMEBREW_PREFIX "/opt/homebrew"
    if test -d "$HOMEBREW_PREFIX";
        set -gx HOMEBREW_CELLAR "$HOMEBREW_PREFIX/Cellar"
        set -gx HOMEBREW_REPOSITORY "$HOMEBREW_PREFIX"
        fish_add_path --global --move --path "$HOMEBREW_PREFIX/bin" "$HOMEBREW_PREFIX/sbin";
        set --local homebrew_man_path "$HOMEBREW_PREFIX/share/man"
        if not contains $homebrew_man_path $MANPATH
            set -gx --append MANPATH $homebrew_man_path
        end
    else
        echo "WARNING: Homebrew not installed in expected location: $HOMEBREW_PREFIX"
    end

end

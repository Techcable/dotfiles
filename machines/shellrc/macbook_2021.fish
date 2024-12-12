# Configuration for my 2021 Macbook Pro
set --local HOMEBREW_ROOT "/opt/homebrew"

set -gx MACHINE_NAME macbook-2021
set -gx MACHINE_NAME_SHORT macbook

# Automatically uses the default browser
#
# TODO: When using OpenIn, this shows a popup menu
# which may be undesirable.
set -gx BROWSER "/usr/bin/open"

function warning
    echo "$(set_color --bold yellow)WARNING:$(set_color reset)" $argv >&2;
end
function error
    echo "$(set_color --bold red)ERROR:$(set_color reset)" $argv >&2;
end

begin
    set --local homebrew_java    set --local homebrew_java_home "$homebrew_java/Contents/Home"
    set --local fallback_java_home "/Library/Java/JavaVirtualMachines/zulu-21.jdk/Contents/Home"
    function consider_jdk
        argparse --min-args=1 --max-args=1 'required-version=' -- $argv
        or return
        set target_java $argv[1]
        set target_java_home "$target_java/Contents/Home"
        if not test -d "$target_java"
            warning "Failed to find JDK: $target_java"
            return 1
        end
        # NOTE: Invoking `java -version` can be _slow_ (~18ms)
        if set -q _flag_required_version
            set --local required_version $_flag_required_version
            set --local --export JAVA_HOME $target_java_home
            java -version 2>&1 | head -1 | string match --quiet --regex 'version ["](?<detected_major_version>\d+).*["]'
            if test $pipestatus[-1] -ne 0
                warning "Failed to detect java version (version pattern doesn't match)"
                return 2
            end
            if test $detected_major_version -ne $required_version
                warning "Skipping JDK $(basename $target_java), because actual version $detected_major_version != required version $required_version"
                return 1
            end
        end
        # Good enough for us :)
        set --export --global JAVA_HOME $target_java_home
        return 0
    end
    # Detect the desired JDK implementation
    #
    # TODO: Use proper JDK version detection
    for jdk in /Library/Java/JavaVirtualMachines/{homebrew-openjdk,zulu-21.jdk}
        consider_jdk $jdk
        if test $status -eq 0
            break
        end
    end
    set --erase consider_jdk
end

begin
    set --local haxe_std_path /opt/homebrew/lib/haxe/std
    if test -d $haxe_std_path
        set -gx HAXE_STD_PATH $haxe_std_path
    else
        warning "Expected haxe stdlib at `$haxe_std_path`"
    end
end

# pipx
fish_add_path --global ~/.local/bin

# APPS: dict[str, AppAction] = {
#    "Keybase": AddSupportBins(expected_bins=("keybase",)),
#    "Sublime Merge": AddSupportBins(expected_bins=("smerge",)),
#    "Sublime Text": AddSupportBins(expected_bins=("subl",)),
#    "Texifier": AppAction.SETUP_ALIAS,

# Sublime Text and Keybase seem to already have added themselves
# to the path, making the old and complicated code to
# 'add application support bins' redundant.
#
# Sublime Text made a symlink from Sublime Text.app/.../subl => /usr/bin/subl
# Keybase added an entry to /etc/paths.d
#
# For texifier, we just use an alias to the `open` command
#
# This removes the need to use the very slow `defaults read`
# command to parse info.plist.
# This correspondingly avoids the need for an SQLite cache
alias texifier="open -a Texifier"


function detect_homebrew_info
    argparse --min-args=1 --max-args=1 'm/mode=' -- $argv
    or return
    set --local binary $argv[1]

    set --local resolved_binary $(readlink $binary)
    if test $status -ne 0
        error "Failed to readlink `$binary`"
        return 1
    end

    string match --quiet --regex "^[\.]{2}/Cellar/(?<pkgname>[^/@]+)(?:@(?<formulaversion>[^/]+))?/(?<fullversion>[^/]+)" "$resolved_binary"
    if test $status -ne 0
        error "Failed to match pattern: `$resolved_binary`"
        return 1
    end
    switch $_flag_mode
        case precise_version
            echo $fullversion
        case formula_version
            echo $formulaversion
        case pkg_name
            echo $pkgname
        case "*"
            error "Unknown mode `$_flag_mode`"
            return 1;
    end
end

# Override pipx default python
#
# Otherwise it will hardcode against a specific minor version like:
# /opt/homebrew/Cellar/python@3.11/3.11.2/Frameworks/Python.framework/Versions/3.11/bin/python3.11
#
# Using that would cause problems when minor version upgrades
begin
    set --local generic_python_binary "/opt/homebrew/bin/python3"
    set --local python_formula_version $(detect_homebrew_info --mode=formula_version "$generic_python_binary")
    if test $status -ne 0
        error "Unable to detect formula version of `$generic_python_binary`";
    else
        set --local versioned_binary "/opt/homebrew/bin/python$python_formula_version"
        if test -x $versioned_binary;
            set --global --export PIPX_DEFAULT_PYTHON $versioned_binary
        else
            set --local reason "is not executable"
            if not test -f $versioned_binary
                set reason "does not exist"
            end
            error "Versioned binary for python@$python_formula_version $reason: `$versioned_binary`"
        end
    end
end

function extend_path
    # TODO: Unify with the "helper function" that does the same thing?
    #
    # NOTE: $(fish_opt --long-only --short=i --long 'ignore-missing') ==> "i-ignore-missing"
    argparse --min-args=1 --max-args=1 'variable=' 'name=' 'order=' 'i-ignore-missing' -- $argv
    or return
    set --local target_dir $argv[1]
    if set -q _flag_variable
        set -f var_name $_flag_variable
    else
        set -f var_name "PATH"
    end
    if set -q _flag_name
        set -f value_name $_flag_name
    else
        set -f value_name "directory"
    end
    set -f extra_flags
    switch $_flag_order
        case "append" ""
            # NOTE: This is the default behavior, unlike
            # fish_add_paths which defaults to --prepend
            set --append extra_flags "--append"
        case "prepend"
            set --append extra_flags "--prepend"
        case "append_system" "append-system"
            if test $var_name != "PATH"
                error "Can only use --where=append_system when --variable=\$PATH (not $var_name)"
                return 1
            end
            # append directly to path (not $fish_user_paths)
            # this means lower priority than system stuff
            set --append extra_flags "--path" "--append"
        case "*"
            error "Invalid --order option: `$_flag_where`"
    end
    if not test -d "$target_dir"
        if set -q _flag_ignore_missing
            return 0
        else
            warning "Missing $value_name: $target_dir"
            return 2
        end
    end
    if test $var_name = "PATH"
        fish_add_path --global $extra_flags -- $target_dir
    else if not contains $target_dir $$var_name
        set --global $extra_flags -- $var_name $target_dir
    end
end

# $GOBIN (used for go install)
extend_path --name='$GOBIN directory' -- "$HOME/go/bin"

# Scala installation managed by "coursier". See here: https://get-coursier.io/docs/cli-overview
extend_path --name="corsier" "$HOME/Library/Application Support/Coursier/bin"

# Verify matlab command points to ~/bin/matlab, which in turn needs to be a symbolic link
# TODO: Is this even useful?
begin
    set --local actual_matlab_path $(command --search matlab)
    if test $status -ne 0
        # matlab not found
    else if test "$actual_matlab_path" != "$HOME/bin/matlab"
        warning "Expected matlab to be in ~/bin, but got `$actual_matlab_path`"
    else if not test -L $actual_matlab_path
        warning "Expected matlab to be a symbolic link: $actual_matlab_path"
    end
end

# Custom $PKG_CONFIG_PATH (to find libraries)

# Homebrew pkg-config path must be explicitly put first, in order to override any future kegs
#
# This way we get homebrew python version instead of keg python version
#
# The default behavior is to have $PKG_CONFIG_PATH override the automatically
# detected libraires (including homebrew libraries).
extend_path --name='homebrew pkgconfig' --variable=PKG_CONFIG_PATH -- "/opt/homebrew/lib/pkgconfig"

extend_path --name='senpai irc client binaries' "/opt/senpai/bin"
extend_path --name='senpai irc client man pages' --variable=MANPATH "/opt/senpai/share/man"

# MacGPG: https://gpgtools.org/
extend_path --name='MacGPG2 /bin dir' "/usr/local/MacGPG2/bin"
extend_path --name='MACGPG manpages' --variable=MANPATH "/usr/local/MacGPG2/share/man"

begin
    set --local current_janet_version $(detect_homebrew_info --mode=precise_version "/opt/homebrew/bin/janet")
    if test $status -ne 0
        warning "Unable to detect homebrew Janet version (is it installed into homebrew cellar?)"
    else
        # add janet-specific bin path (used for janet binary packages)
        extend_path --name='homebrew janet bin' "/opt/homebrew/Cellar/janet/$current_janet_version/bin"
    end
end

# Unversioned python provided by homebrew
#
# Resolves a strange conflict with a 'pip' command for wrong version
extend_path --name='unversioned python bin' "/opt/homebrew/opt/python/libexec/bin"


# Some homebrew things are "keg-only" meaning they are not on the path by default
#
# Usually these are alternative versions of the main package.
# Particular examples are lua@5.3 and python@3.10
#
# We want these on the path, but we want them at the end (lower precedence)
# so they don't conflict with existing versions
#
# Use the extend_path builtin to add it to the end (but only if the keg exists)
function detect_keg
    argparse --min-args=1 --max-args=1 'b-bin-order=' 'p-pkgconfig-order=' 'i-ignore-missing-pkgconfig' -- $argv
    set -f name $argv[1]
    set -f keg_prefix "/opt/homebrew/opt"
    set -f keg_bin "$keg_prefix/$name/bin"
    set -f extra_args_bin
    set -f extra_args_pkgconfig
    if set -q _flag_bin_order
        set --append extra_args_bin "--order=$_flag_bin_order"
    end
    if set -q _flag_pkgconfig_order
        set ---append extra_args_pkgconfig "--order=$_flag_pkgconfig_order"
    end
    if set -q _flag_ignore_missing_pkgconfig
        set --append extra_args_pkgconfig '--ignore-missing'
    end
    extend_path --name="keg $name `/bin` dir" $extra_args_bin -- "$keg_prefix/$name/bin"
    extend_path --name="keg $name pkgconfig directory" $extra_args_pkgconfig --variable=PKG_CONFIG_PATH -- "$keg_prefix/$name/lib/pkgconfig"
end

detect_keg "lua@5.3"
# Detect LLVM keg. This is nessicary because homebrew llvm
# has some utilities that system LLVM does not have (like clang-format and )
#
# This is lower priority than system LLVM,
# so system clang will be prefered over homebrew clang.
# This only makes a difference for those
# specific tools that are missing in the system installation.
#
# This seems likely to cause issues with mismatches between homebrew LLVM/clang
# and system LLVM/clang. However, I need clang-format (which is only in Homebrew)
# and right now I still want to keep using the system clang,
# so we are stuck with this
detect_keg --bin-order='append-system' --ignore-missing-pkgconfig "llvm"

# Mac has no LDD command
#
# See here: https://discussions.apple.com/thread/309193 for suggestion
# Also "Rosetta stone for Unixes"
function lld -d='Alias for otool -L' --wraps="otool -L"
    echo "NOTE: Using otool -L"
    otool -L $argv
end

if command --query "pacaptr"
    alias pacman=pacaptr
end

# opam configuration
source /Users/nicholas/.opam/opam-init/init.fish > /dev/null 2> /dev/null; or true

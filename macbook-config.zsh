# Configuration for my 2021 Macbook Pro

export MACHINE_NAME="macbook-2021"

# Automatically uses the default browser
export BROWSER="/usr/bin/open"

local preferred_java_version=17
local preferred_java_home=$(fd "jdk-${prefered_java_version}.*\.jdk" /Library/Java/JavaVirtualMachines --maxdepth 1)
if [[ -d "$preferred_java_home/Contents/Home" ]]; then
    export JAVA_HOME="${preferred_java_home}/Contents/Home";
fi

# Rust binaries
#
# NOTE: This contains almost all the binaries in ~/.rustup/toolchain/<default toolchain>/bin
extend_path ~/.cargo/bin
# My private bin ($HOME/bin) 
extend_path ~/bin
# Keybase path
extend_path /Applications/Keybase.app/Contents/SharedSupport/bin

# Where pip install puts console_script executables
extend_path "/opt/homebrew/Frameworks/Python.framework/Versions/Current/bin"

# TODO: This is contorted to fit the zsh2xonsh parser :(
local preferred_python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
# Where pip install puts (user) console_script executables
extend_path "$HOME/Library/Python/${preferred_python_version}/bin"

# Custom $PKG_CONFIG_PATH (to find libraries)

# Homebrew pkg-config path must be explicitly put first, in order to override any future kegs
#
# This way we get homebrew python version instead of keg python version
#
# The default behavior is to have $PKG_CONFIG_PATH override the automatically
# detected libraires (including homebrew libraries).
extend_path "/opt/homebrew/lib/pkgconfig" PKG_CONFIG_PATH

# Criterion: a unit testing framework for C - https://github.com/Snaipe/Criterion
extend_path "/opt/criterion/lib/pkgconfig" PKG_CONFIG_PATH

# Zig: Installed to /opt/zig so I can experiment with latest development versions :)
extend_path "/opt/zig/bin"

# Some homebrew things are "keg-only" meaning they are not on the path by default
#
# Usually these are alternative versions of the main package.
# Particular examples are lua@5.3 and python@3.10
#
# We want these on the path, but we want them at the end (lower precedence)
# so they don't conflict with existing versions
#
# Use the extend_path builtin to add it to the end (but only if the keg exists)
function detect_keg() {
    local keg_prefix="/opt/homebrew/opt";
    if [[ -d "${keg_prefix}/$1/bin" ]]; then
        # echo "Detected keg $1";
        extend_path "${keg_prefix}/$1/bin"
    fi
    if [[ -d "${keg_prefix}/$1/lib/pkgconfig" ]]; then
        extend_path "${keg_prefix}/$1/lib/pkgconfig" PKG_CONFIG_PATH
    fi
}
detect_keg "python@3.10"
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
detect_keg "llvm"

# Mac has no LDD command
#
# See here: https://discussions.apple.com/thread/309193 for suggestion
# Also "Rosetta stone for Unixes"
alias ldd="echo 'Using otool -L' && otool -L"

# NOTE: Prefix with 'py' to indicate we are in xonsh
# We really should be prefixing with 'xonsh', but 'py' is shorter
# It's not really ambiguous, since this is really the python-prompt (for all
# intents and purposes)
# I'm not going to confuse with the regular python interpreter (python3) cause i'll
# know its a shell
export XONSH_PREFIX="py"
export XONSH_PREFIX_COLOR="yellow"

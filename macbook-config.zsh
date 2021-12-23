# Configuration for my 2021 Macbook Pro

# Automatically uses the default browser
export BROWSER="/usr/bin/open"

local preferred_java_version=17
local preferred_java_home=$(fd "jdk-${prefered_java_version}.*\.jdk" /Library/Java/JavaVirtualMachines --maxdepth 1)
if [[ -d "$preferred_java_home/Contents/Home" ]]; then
    export JAVA_HOME="${preferred_java_home}/Contents/Home";
fi

extend_path ~/.cargo/bin
# My private bin ($HOME/bin) 
extend_path ~/bin
# TODO: I really don't like hardcoding these
extend_path ~/.rustup/toolchains/nightly-aarch64-apple-darwin/bin

# NOTE: Prefix with 'py' to indicate we are in xonsh
# We really should be prefixing with 'xonsh', but 'py' is shorter
# It's not really ambiguous, since this is really the python-prompt (for all
# intents and purposes)
# I'm not going to confuse with the regular python interpreter (python3) cause i'll
# know its a shell
export XONSH_PREFIX="py"
export XONSH_PREFIX_COLOR="yellow"

# ================= WARNING  =================== #
# This file is version controled (and public)    #
# Do not store secret information here. Instead, #
# Use ~/.secrets.json or ~/keys/secrets.json     #
# ============================================== #
#
# See also ~/.xonshrc and the warning there
# See also ~/.config.toml for settings

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

# Path to your oh-my-zsh installation.
# Use "local" oh-my-zsh file if no global one exists
if [[ -e /usr/share/oh-my-zsh ]]; then
    export ZSH=/usr/share/oh-my-zsh
else
    export ZSH=$HOME/.oh-my-zsh
fi

# Set name of the theme to load. Optionally, if you set this to "random"
# it'll load a random theme each time that oh-my-zsh is loaded.
# See https://github.com/robbyrussell/oh-my-zsh/wiki/Themes

# ZSH_THEME="agnoster" # Dark
ZSH_THEME="robbyrussell" # Light

# Set list of themes to load
# Setting this variable when ZSH_THEME=random
# cause zsh load theme from this variable instead of
# looking in ~/.oh-my-zsh/themes/
# An empty array have no effect
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion. Case
# sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment the following line to disable bi-weekly auto-update checks.
# DISABLE_AUTO_UPDATE="true"

# Uncomment the following line to change how often to auto-update (in days).
# export UPDATE_ZSH_DAYS=13

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# The optional three formats: "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
  gitfast
  # Programming Languages
  cargo
  rust
  rustup
)

source $ZSH/oh-my-zsh.sh

# User configuration

# We load our configuration from a ~/.config.toml file.
# If that's not found, we just print a warning and exit
#
# This requires 'tomli' to work,
# and converts from toml -> json for further manipulation with jq
#
# Yes this is horrible (but what am I supposed to do?)

function warning() {
    
    echo "${fg_bold[yellow]}WARNING:${reset_color} $1" >&2;
}

if which tomlq >/dev/null; then
    TOMLQ=$(which tomlq)
elif [ -x ~/bin/tomlq ]; then
    TOMLQ=~/bin/tomlq
else
    warning "Cannot find `tomlq` command, cannot parse ~/.config.toml"
    warning "Consider installing it https://github.com/Techcable/tomlq"
    TOMLQ="";
fi

if [ -x "$TOMLQ" ]; then
    for pth in $($TOMLQ -r '.path[]? | sub("~"; $ENV.HOME)' ~/.config.toml); do
        export PATH="$PATH:$pth";
    done
fi

if [ $(uname) = "Darwin" ]; then
    if [ -x /opt/homebrew/bin/brew ]; then
        # TODO: Security?
        # TODO: This should be done via config, not auto-detection.
        echo "Setting up homebrew...";
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi;
    alias python=python3
    alias pip=pip3
fi



# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Use neovim
export EDITOR="nvim"

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# ssh
# export SSH_KEY_PATH="~/.ssh/rsa_id"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

## Pyenv configuration
#export PYENV_ROOT="$HOME/.pyenv"
#eport PATH="$PYENV_ROOT/bin:$PATH"

## PyEnv initialization
# NOTE: This is supposed to be near the end since it manipulates PATH
# NOTE: Intentionlly disabled
# if command -v pyenv 1>/dev/null 2>&1; then
#   eval "$(pyenv init -)"
# fi

# Fix GPG error "Inappropriate ioctl for device"
# See stackoverflow: https://stackoverflow.com/a/41054093
export GPG_TTY=$(tty)

# Better time command
# See stackoverflow: https://superuser.com/a/767491
TIMEFMT='%J   %U  user %S system %P cpu %*E total'$'\n'\
'avg shared (code):         %X KB'$'\n'\
'avg unshared (data/stack): %D KB'$'\n'\
'total (sum):               %K KB'$'\n'\
'max memory:                %M MB'$'\n'\
'page faults from disk:     %F'$'\n'\
'other page faults:         %R'

alias paper='. /home/nicholas/git/Paper/paper'

# Prefer exa to ls
alias ls='exa'
alias lsa='exa -a'

# Alias cp to prefer reflinks
# We are using Btrfs :D
#
# NOTE: Now unnecessary due to cp version 9.0 
#
# CP_VERSION="$(cp --version | rg 'cp .* (\d+\.\d+)' -r '$1')"
# CP_MAJOR_VERSION=$(echo $CP_VERSION | rg '(\d+)\.(\d+)' -r '$1')
# CP_MINOR_VERSION=$(echo $CP_VERSION | rg '(\d+)\.(\d+)' -r '$2')
# FILESYSTEM_TYPE="$(df --output=fstype ~ | grep -v 'Type')"
# if [ $FILESYSTEM_TYPE != 'btrfs' ]; then
#    echo "${fg[red]}Using unexpected filesystem type: $FILESYSTEM_TYPE" >&2;
#    echo "${fg[red]}Expected 'btrfs' for fast COW" >&2;
# elif [[ $CP_MAJOR_VERSION -gt 8 || $CP_MINOR_VERSION -gt 32 ]]; then
#    echo "${fg[yellow]}Detected CP version: $CP_VERSION > 8.32" >&2;
#    echo "${fg[yellow]}GNU cp ${CP_VERSION} likely has --reflink=auto as default" >&2;
#    echo "${fg[yellow]}  - See coreutils commit: https://github.com/coreutils/coreutils/commit/25725f9d417"
#else
#    echo "Overding cp to use ${bold_color}COW${reset_color} by default (btrfs)";
#    alias cp='cp --reflink=auto';
#fi;

# Extra aliases when running under kitty
# Does this override scripts that run 'diff'?
if [ $TERM = "xterm-kitty" ]; then
    alias icat="kitty +kitten icat"
    alias diff="kitty +kitten diff"

    # Need to fix ssh for kitty
    alias ssh="kitty +kitten ssh"
fi;


# Override browser
if [ -x "$TOMLQ" ]; then
    export BROWSER=$($TOMLQ -r '.browser' ~/.config.toml);
fi

function extract_secret() {
    local key="$1";
    local secret_file="$HOME/keys/secrets.json";
    if [ ! -e $secret_file ]; then
        secret_file="$HOME/.secrets.json";
    fi
    if [ -e $secret_file ]; then
        jq -e ".$key" "$secret_file";
    else
        return 1;
    fi
}

# Bitwarden API Key
# NOTE: Master password is still needed for decryption
BW_CLIENTID=$(extract_secret "bitwarden.client_id");
BW_CLIENTSECRET=$(extract_secret "bitwarden.client_secret");

function print_stars() {
    # TODO: Should we subtract one from the colomn?
    # I am just doing this because I don't trust `tput`
    python -c "print('*' * ( $(tput cols) - 1 ))";
}


# Give us a 'zsh' indicator before our prompt
OLD_PROMPT="$PROMPT"
# NOTE: Must escape with %{fg[magenta%} or it'll get all confused about
# cursor position: https://code-examples.net/en/q/796bbb
export PROMPT="%{$fg[magenta]%}zsh$OLD_PROMPT"

# By default, give a random chance of switching to xonsh
if [ -n $XONSH_RANDOM_CHANCE ]; then
    export XONSH_RANDOM_CHANCE=0.90;
fi
if [[ $(python -c 'import random; print(random.random())') -lt $XONSH_RANDOM_CHANCE ]]; then
    print_stars
    echo -e "Automatically switching from ${fg_bold[magenta]}zsh${reset_color} -> ${fg_bold[yellow]}xonsh${reset_color}: https://xon.sh/";
    python -c "print(f'As determined by random chance of {($XONSH_RANDOM_CHANCE * 100):.1f}%')";
    echo -e "Press ${fg_bold[grey]}ctrl-d${reset_color} at any time to exit back to zsh" 
    export SKIP_XONSH_STARTUP_MESSAGES="cp";
    xonsh; # Switching
else
# NOTE: Prompt about switching to xonsh
print_stars
echo -e "Remember the power of ${fg_bold[yellow]}xonsh${reset_color}: https://xonsh.sh"
echo "It uses Python \u2764\uFE0F"
print_stars
fi;


# WARNING: Remember to put path extensions **before** the test for trusted commands

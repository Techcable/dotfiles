# NOTE: Must stay in sync with common.py

# NOTE: Intentionally skipped
(let [env-var (os/getenv "DOTFILES_PATH")]
    (assert= DOTFILES-PATH env-var "Variable not set: $DOTFILES_PATH")
    (assert=
        (os/stat DOTFILES-PATH :mode)
        :directory
        "Unable to find dotfiles directory: ${env-var}"
    ))

# Rust binaries
#
# NOTE: This contains almost all the binaries in ~/.rustup/toolchain/<default toolchain>/bin
(extend-path (string HOME "/.cargo/bin"))
# My private bin ($HOME/bin)
(extend-path (string HOME "/bin"))

# add dotfiles scripts directory
#
# These are convenient scripts I want to sync across all
# my computers
(extend-path (string DOTFILES-PATH "/scripts"))

# I like neovim
(export "EDITOR" "nvim")

# See stackoverflow: https://stackoverflow.com/a/41054093
(export "GPG_TTY" (shell/process ["tty"]))

# Add jetbrains user_config (if platform is not a desktop)
(def- is-desktop (nil? (string/find "server" MACHINE-NAME)))
(when is-desktop
    (def user-data (case (os/which)
        :macos (string HOME "/Library/Application Support")
        (string HOME "/.local/share")))
    (def jetbrains-app-dir (string user-data "/Jetbrains/Toolbox/scripts"))
    (if (dir-exists? jetbrains-app-dir)
        (extend-path jetbrains-app-dir)
        (warning (string/format "could not find jetbrains script directory: %q" jetbrains-app-dir))))

# Have pip-run cache its created environments
#
# https://github.com/jaraco/pip-run#environment-persistence
#
# TODO: This may eventually result in bloat :/
# It is never cleaned up.
(export "PIP_RUN_MODE" "persist")

# Extra aliases when running under kitty
#
# TODO: Is this redundant with kitty's new shell integration?
# https://sw.kovidgoyal.net/kitty/shell-integration/
(when (= (os/getenv "TERM") "xterm-kitty")
    (alias icat "kitty +kitten icat" :wraps :updated)
    (alias diff "kitty +kitten diff" :wraps :updated)

    # Need to fix ssh for kitty
    #
    # NOTE: Do *not* use kitty for regular ssh
    #
    (alias "kitty-ssh" "kitty +kitten ssh" :wraps :updated))

# Alias ranger -> r for easier access
(if (which-command "ranger")
    (alias "r" "ranger" :wraps :updated)
    (warning "The 'ranger' file manager is not installed"))
if command --query "ranger"
    alias r="ranger"
else
    warning "The 'ranger' file manager is not installed"
end

if command --query betterstat
    alias stat=betterstat
else
    warning "Missing `betterstat` command"
end

# Prefer lsd to ls
#
# We used to use `exa`,
# but that is now second priority
if command --query "lsd"
    alias ls="lsd"
    alias lsa="lsd -A"

    # Shortcuts for seeing sizes
    alias "lsds"="lsd -A --blocks size,name"
    alias "lsdl"="lsd -A --long"

    # Override tree command with `lsd --tree` (more consistent)
    alias "tree"="lsd --tree"
else if command --query "exa"
    warning "Missing lsd (but has `exa` installed)"
else
    warning "Cannot find lsd or exa"
end

# Warn on usage of bpytop
if command --query "bpytop"
    set --local real_bpytop $(command --search "bpytop")
    if command --query "btop"
        function bpytop --wraps bpytop --inherit-variable real_bpytop
            echo "$(set_color --bold yellow)NOTE:$(set_color reset) Please consider using btop"
            command $real_bpytop
        end
    else
        warning "bpytop is installed, but not btop"
    end
else
    warning "bpytop is not installed"
end

begin
    set --local dotfiles_python_libs "$DOTFILES_PATH/libs/python"
    if not test -d "$dotfiles_python_libs"
        warning "Missing dotfiles python libs: $dotfiles_python_libs"
    else if not contains $dotfiles_python_libs $PYTHONPATH
        set --global --append PYTHONPATH $dotfiles_python_libs
    end
end

begin
    set --local legacy_config "$HOME/.shell-config.rc"
    if test -e "$legacy_config"
        warning "Legacy config file should not exist: $legacy_config"
    end
end


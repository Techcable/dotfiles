"""Default configuration shared across all machines"""
(import os)
(import shutil)
(import sys)
(import pathlib [Path])
(import subprocess [PIPE run])

(try
    (assert (= DOTFILES_PATH (Path (get os.environ "DOTFILES_PATH"))))
    (except [KeyError]
        (warning "Missing $DOTFILES_PATH environment variable")))

; Rust binaries
;
; NOTE: This contains almost all the binaries in ~/.rustup/toolchain/<default toolchain>/bin
(extend_path "~/.cargo/bin")
; My private bin ($HOME/bin)
(extend_path "~/bin")

; add dotfiles scripts directory
;
; These are convenient scripts I want to sync across all
; my computers
(extend_path (/ DOTFILES_PATH "scripts"))

; I like neovim
((do export) "EDITOR" "nvim")

; nasty compat symlinks (NOTE: This counts the number of 'True' == 1 symlinks)
(let [num_compat_symlinks (sum
    (gfor path (. DOTFILES_PATH (iterdir)) (and (. path (is_symlink)) (= (. path suffix) ".py"))))]
    (when num_compat_symlinks
        (todo 
            "Get rid of nasty compat symlinks in the root directory"
            f"({(set_color "yellow")}{num_compat_symlinks}{(reset_color)} symlinks remaining)")))

; Fix GPG error "Inappropriate ioctl for device"
; See stackoverflow: https://stackoverflow.com/a/41054093
((do export) "GPG_TTY" (. (run ["tty"] :stdout PIPE :encoding "utf8") stdout (rstrip)))

; Add jetbrains user_config
(if (. PLATFORM (is_desktop))
    (try
        (let [jetbrains_app_dir
            (/ (. AppDir USER_CONFIG (resolve PLATFORM)) "Jetbrains/Toolbox/scripts")]
            (if jetbrains_app_dir
                (extend_path jetbrains_app_dir)
                (raise (FileNotFoundError f"could not find directory {jetbrains_app_dir}"))))
        (except [e [UnsupportedPlatformError FileNotFoundError]]
            (warning f"While attempting to detect jetbrains script path, {(str e)}")))
    (debug "Not a desktop"))

; Extra aliases when running under kitty
;
; TODO: Is this redundant with kitty's new shell integration?
; https://sw.kovidgoyal.net/kitty/shell-integration/
(when (= (. os (getenv "TERM")) "xterm-kitty")
    (alias "icat" "kitty +kitten icat")
    (alias "diff" "kitty +kitten diff")

    ; Need to fix ssh for kitty
    (alias "ssh" "kitty +kitten ssh"))


; Prefer exa to ls
(when (. shutil (which "exa"))
    (alias "ls" "exa")
    (alias "lsa" "exa -a"))

; Warn on usage of bpytop
(if (setx real_bpytop (. shutil (which "bpytop")))
    (if (. shutil (which "btop"))
        (alias
            "bpytop"
            f"{real_bpytop}; echo \"{(set_color "yellow" :bold True)}NOTE{(reset_color)}: Please consider using btop\""
        )
        (warning "bpytop is installed, but not btop"))
    (warning "bpytop is not installed"))

; This is xonsh-specific (not even sure why it's here)
;
; We Prefix with 'py' to indicate we are in xonsh
; We really should be prefixing with 'xonsh', but 'py' is shorter
; It's not really ambiguous, since this is really the python-prompt (for all
; intents and purposes)
; I'm not going to confuse with the regular python interpreter (python3) cause i'll
; know its a shell
;
; This is the default value for
((do export) "XONSH_PREFIX" "py")
((do export) "XONSH_PREFIX_COLOR" "yellow")

; Configuration for my 2021 Macbook Pro
(import re)
(import shlex)
(import shutil)
(import sys)
(import pathlib [Path])
(import subprocess [PIPE CalledProcessError run])
(import typing [Callable])

(defreader p
    (let [text (.parse_one_form &reader)]
        `(Path ~text)))

(defmacro unless [arg #* forms]
    `(when (not ~arg) ~forms))

((do export) "MACHINE_NAME" "macbook-2021")
((do export) "MACHINE_NAME_SHORT" "macbook")

; Automatically uses the default browser
((do export) "BROWSER" #p"/usr/bin/open")

(unless (. PLATFORM (is_desktop))
    (warning "Expected a desktop environment for macbook!"))

(let [preferred_java_version 17]
    (setv preferred_java_home None)
    (for [java_home (.iterdir #p "/Library/Java/JavaVirtualMachines")]
        (let [m (re.match "jdk-(\\d+)[.\\d]*\\.jdk$" (. java_home name))]
            (when (and (not? m None) (= (int (. m (group 1))) preferred_java_version))
                (setv preferred_java_home java_home)
                (break))))
    (cond
        (is preferred_java_home None) (warning "Unable to detect java version")
        (.is_dir (/ preferred_java_home "Contents/Home")) (do
            ((do export) "JAVA_HOME" (/ preferred_java_home "Contents/Home")))))

(let [haxe_std_path #p "/opt/homebrew/lib/haxe/std"]
    (if (.is_dir haxe_std_path)
        ((do export) "HAXE_STD_PATH" haxe_std_path)
        (warning f"Expected haxe stdlib: {haxe_std_path}")))

; Keybase path
(extend_path "/Applications/Keybase.app/Contents/SharedSupport/bin")

(for [app_name ["Keybase" "Sublime Text" "Texifier"]]
    (setv app_root #p f"/Applications/{app_name}.app")
    (unless (.is_dir app_root)
        (warning f"Unable to find application {app_name}: Missing directory {app_root!r}"))
    ; TODO: Cache this?
    (try
        (setv executable_name (. (run
            ["defaults" "read" (str (/ app_root "Contents/Info")) "CFBundleExecutable"]
            :check True
            :stdout PIPE
            :encoding "utf-8"
        ) stdout (rstrip)))
        (except [CalledProcessError]
            (warning f"Unable to detect executable name for {app_root!r}")
            (continue)))

    (setv support_bin_dir (/ app_root "Contents/SharedSupport/bin"))
    (setv main_bin_path (/ app_root "Contents/MacOS" executable_name))
    (cond
        (not (.is_file main_bin_path))
            (warning f"Missing binary path for {app_name}: {main_bin_path!r}")
        (.is_dir support_bin_dir) (extend_path support_bin_dir)
        True (alias
            (. executable_name (lower) (replace "_" "-") (replace " " "-"))
            (run_in_background_helper [(str main_bin_path)]))))


; Where pip install puts console_script executables
(extend_path "/opt/homebrew/Frameworks/Python.framework/Versions/Current/bin")

; NOTE: Assumes that current python version is the 'preferred' one
;
; also 'preffered' is not a good name:
; if it is preferred that doesn't mean it is the one we should be pointing to
; for pip purposes ....
;
; If any of this is not the case, we need to setup some sort of config file
; not going back to spawning subprocesses
(let [preferred_python_version (. "." (join (map str (cut (. sys version_info) 2))))]
    ; Where pip install puts (user) console_script executables
    ;
    ; TODO: Is this obseleted by pipx?
    (extend_path (/ (. Path (home)) f"Library/Python/{preferred_python_version}/bin")))

; pipx
(extend_path "~/.local/bin")  ; path for pipx

; Scala installation managed by "coursier". See here: https://get-coursier.io/docs/cli-overview
(extend_path "~/Library/Application Support/Coursier/bin")

; Python 3.11 (beta builds)
;
; TODO: Remove this once 3.11 becomes stable
(extend_path "/Library/Frameworks/Python.framework/Versions/3.11/bin")

; Custom $PKG_CONFIG_PATH (to find libraries)

; Homebrew pkg-config path must be explicitly put first, in order to override any future kegs
;
; This way we get homebrew python version instead of keg python version
;
; The default behavior is to have $PKG_CONFIG_PATH override the automatically
; detected libraires (including homebrew libraries).
(extend_path "/opt/homebrew/lib/pkgconfig" "PKG_CONFIG_PATH")

; Criterion: a unit testing framework for C - https://github.com/Snaipe/Criterion
(extend_path "/opt/criterion/lib/pkgconfig" "PKG_CONFIG_PATH")

; senpai IRC client (CLI): https://sr.ht/~taiite/senpai/
(extend_path "/opt/senpai/bin")
(extend_path "/opt/senpai/share/man" "MANPATH")

; MacGPG: https://gpgtools.org/
(extend_path "/usr/local/MacGPG2/bin")
(extend_path "/usr/local/MacGPG2/share/man" "MANPATH")

; stacked git: https://stacked-git.github.io
(extend_path "/opt/stgit/bin")
(extend_path "/opt/stgit/share/man" "MANPATH")

; Calling `brew list --versions janet` takes 500 ms,
; using `janet -v` takes 5ms
;
; However even faster to skip subprocess detection
; and rely on homebrew directory structure
(do
    (defn detect_janet_version []
        (try
            (setv janet_exe_path (.readlink (Path (. shutil (which "janet")))))
            (except [OSError]
                (return None)))

        (setv m (re.fullmatch r"../Cellar/janet/([^/]+)/bin/janet" (str janet_exe_path)))
        (return (if (not? m None)
            (. m (group 1))
            None)))

    (setx current_janet_version (detect_janet_version))
    (when (is current_janet_version None)
        (warning "Unable to detect Janet version based on PATH (is it installed into homebrew cellar?)"))

    (del detect_janet_version) ; TODO: Is this scoping needed?

    (if (not? current_janet_version None)
        ; add janet-specific bin path (used for janet binary packages)
        (extend_path f"/opt/homebrew/Cellar/janet/{current_janet_version}/bin")
        (warning "Missing janet version")))


; Some homebrew things are "keg-only" meaning they are not on the path by default
;
; Usually these are alternative versions of the main package.
; Particular examples are lua@5.3 and python@3.10
;
; We want these on the path, but we want them at the end (lower precedence)
; so they don't conflict with existing versions
;
; Use the extend_path builtin to add it to the end (but only if the keg exists)
(defn detect_keg [#^str name * #^PathOrderSpec [order None]]
    (setv keg_prefix #p "/opt/homebrew/opt")
    (when (.is_dir (setx keg_bin (/ keg_prefix f"{name}/bin")))
        ; echo "Detected keg $1";
        (extend_path keg_bin :order order))

    (when (.is_dir (setx keg_pkgconfig (/ keg_prefix f"{name}/lib/pkgconfig")))
        (extend_path keg_pkgconfig "PKG_CONFIG_PATH" :order order)))



(detect_keg "python@3.10")
(detect_keg "lua@5.3")
; Detect LLVM keg. This is nessicary because homebrew llvm
; has some utilities that system LLVM does not have (like clang-format and )
;
; This is lower priority than system LLVM,
; so system clang will be prefered over homebrew clang.
; This only makes a difference for those
; specific tools that are missing in the system installation.
;
; This seems likely to cause issues with mismatches between homebrew LLVM/clang
; and system LLVM/clang. However, I need clang-format (which is only in Homebrew)
; and right now I still want to keep using the system clang,
; so we are stuck with this
(detect_keg "llvm" :order PathOrderSpec.APPEND_SYSTEM)

; Mac has no LDD command
;
; See here: https://discussions.apple.com/thread/309193 for suggestion
; Also "Rosetta stone for Unixes"
(alias "ldd" "echo 'Using otool -L' && otool -L")

(when (not? (. shutil (which "pacaptr")) None)
    ; alias pacaptr
    (alias "pacman" "pacaptr"))

; Sometimes my macbook only has python3 on $PATH, not python
;
; Python Environment: https://xkcd.com/1987/
;
; TODO: Has this happened recently?
(when (is (. shutil (which "python")) None)
    (alias "python" "python3"))

# Configuration for my 2021 Macbook Pro
import shlex
import shutil
import sys
from pathlib import Path
from subprocess import PIPE, CalledProcessError, run

export("MACHINE_NAME", "macbook-2021")
export("MACHINE_NAME_SHORT", "macbook")

# Automatically uses the default browser
export("BROWSER", Path("/usr/bin/open"))

preferred_java_version = 17
try:
    preferred_java_home = Path(
        run(
            [
                "fd",
                f"jdk-{preferred_java_version}.*\\.jdk",
                "/Library/Java/JavaVirtualMachines",
                "--maxdepth",
                "1",
            ],
            check=True,
            stdout=PIPE,
            encoding="utf8",
        ).stdout.rstrip()
    )
except CalledProcessError as f:
    warning("Unable to detect java version")
    preferred_java_home = None
else:
    if (preferred_java_home / "Contents/Home").is_dir():
        export("JAVA_HOME", preferred_java_home / "Contents/Home")

# Keybase path
extend_path("/Applications/Keybase.app/Contents/SharedSupport/bin")

for app_name in ["Keybase", "Sublime Text", "Texifier"]:
    app_root = Path(f"/Applications/{app_name}.app")
    if not app_root.is_dir():
        warning("Unable to find application {app_name}: Missing directory {app_root!r}")
    try:
        executable_name = run(
            ["defaults", "read", str(app_root / "Contents/Info"), "CFBundleExecutable"],
            check=True,
            stdout=PIPE,
            encoding="utf8",
        ).stdout.rstrip()
    except CalledProcessError:
        warning(f"Unable to detect executable name for {app_root!r}")
        continue
    support_bin_dir = app_root / "Contents/SharedSupport/bin"
    main_bin_path = app_root / "Contents/MacOS" / executable_name
    if not main_bin_path.is_file():
        warning(f"Missing binary path for {app_name}: {main_bin_path!r}")
    elif support_bin_dir.is_dir():
        extend_path(support_bin_dir)
    else:
        alias(
            executable_name.lower().replace("_", "-").replace(" ", "-"),
            run_in_background_helper([str(main_bin_path)]),
        )


# Where pip install puts console_script executables
extend_path("/opt/homebrew/Frameworks/Python.framework/Versions/Current/bin")

# TODO: Can we just use the python version we're currently executing?
try:
    preferred_python_version = run(
        [
            "python3",
            "-c",
            "import sys; print('.'.join(map(str, sys.version_info[:2])))",
        ],
        check=True,
        stdout=PIPE,
        encoding="utf8",
    ).stdout.rstrip()
except CalledProcessError:
    warning("Unable to detect python version")
    # Fallback to current python version
    preferred_python_version = ".".join(map(str, sys.version_info[:2]))
# Where pip install puts (user) console_script executables
extend_path(Path.home() / f"Library/Python/{preferred_python_version}/bin")

# Scala installation managed by "coursier". See here: https://get-coursier.io/docs/cli-overview
extend_path("~/Library/Application Support/Coursier/bin")

# Python 3.11 (beta builds)
#
# TODO: Remove this once 3.11 becomes stable
extend_path("/Library/Frameworks/Python.framework/Versions/3.11/bin")

# Custom $PKG_CONFIG_PATH (to find libraries)

# Homebrew pkg-config path must be explicitly put first, in order to override any future kegs
#
# This way we get homebrew python version instead of keg python version
#
# The default behavior is to have $PKG_CONFIG_PATH override the automatically
# detected libraires (including homebrew libraries).
extend_path("/opt/homebrew/lib/pkgconfig", "PKG_CONFIG_PATH")

# Criterion: a unit testing framework for C - https://github.com/Snaipe/Criterion
extend_path("/opt/criterion/lib/pkgconfig", "PKG_CONFIG_PATH")

# senpai IRC client (CLI): https://sr.ht/~taiite/senpai/
extend_path("/opt/senpai/bin")
extend_path("/opt/senpai/share/man", "MANPATH")

# MacGPG: https://gpgtools.org/
extend_path("/usr/local/MacGPG2/bin")
extend_path("/usr/local/MacGPG2/share/man", "MANPATH")


# Calling `brew list --versions janet` takes 500 ms,
# prefer `janet -v` which takes 5ms
try:

    def parse_janet_version(output: str):
        import re  # Bizzare name-error if I import this at top of file

        mtch = re.match(r"^([\d\.]+)([-\w]+)$", output)
        if mtch is not None:
            return mtch.group(1)
        else:
            warning("Unable to parse janet version: {output!r}")
            return None

    current_janet_version = parse_janet_version(
        run(
            ["janet", "-v"],
            check=True,
            stdout=PIPE,
            encoding="utf8",
        ).stdout.rstrip()
    )
    del parse_janet_version  # scoping ;)
except CalledProcessError:
    warning("Unable to detect Janet version")
    current_janet_version = None  # AKA "unknown"

if current_janet_version is not None:
    # add janet-specific bin path (used for janet binary packages)
    extend_path(f"/opt/homebrew/Cellar/janet/{current_janet_version}/bin")
else:
    warning("Missing janet version")

# Some homebrew things are "keg-only" meaning they are not on the path by default
#
# Usually these are alternative versions of the main package.
# Particular examples are lua@5.3 and python@3.10
#
# We want these on the path, but we want them at the end (lower precedence)
# so they don't conflict with existing versions
#
# Use the extend_path builtin to add it to the end (but only if the keg exists)
def detect_keg(name: str):
    global Path  # Why is this needed?
    keg_prefix = Path("/opt/homebrew/opt")
    if (keg_bin := keg_prefix / f"{name}/bin").is_dir():
        # echo "Detected keg $1";
        extend_path(keg_bin)
    if (keg_pkgconfig := keg_prefix / f"{name}/lib/pkgconfig").is_dir():
        extend_path(keg_pkgconfig, "PKG_CONFIG_PATH")


detect_keg("python@3.10")
detect_keg("lua@5.3")
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
detect_keg("llvm")

# Mac has no LDD command
#
# See here: https://discussions.apple.com/thread/309193 for suggestion
# Also "Rosetta stone for Unixes"
alias("ldd", "echo 'Using otool -L' && otool -L")

if shutil.which("pacaptr") is not None:
    # alias pacaptr
    alias("pacman", "pacaptr")

# Sometimes my macbook only has python3 on $PATH, not python
#
# Python Environment: https://xkcd.com/1987/
if shutil.which("python") is None:
    alias("python", "python3")

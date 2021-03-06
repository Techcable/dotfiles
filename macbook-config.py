# Configuration for my 2021 Macbook Pro
import shutil
import sys
from pathlib import Path
from subprocess import PIPE, CalledProcessError, run

export("MACHINE_NAME", "macbook-2021")

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

# Zig: Installed to /opt/zig so I can experiment with latest development versions :)
extend_path("/opt/zig/bin")

# Janet: jpm is installed to /opt/janet
extend_path("/opt/janet/bin")

# srht CLI: https://git.sr.ht/~emersion/hut
extend_path("/opt/srhut/bin")
extend_path("/opt/srhut/share/man", "MANPATH")

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


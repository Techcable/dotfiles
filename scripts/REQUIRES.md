# Requirements
The dependencies for the scripts.

These are libraries you can assume are always
installed, without needing to use `pip-run`.

With some exceptions (those that are seperately installed/managed by the system),
these packages should be installed via `pip install --user` (into the user site-pacakges).

Even if you do use `pip-run`, these dependencies
will already be installed and usable.
NOTE: `pip-run`` always specifies the equivalent `--system-site-packages`.
Specifying them again is redundant and will will
cause .

<!-- NOTE: This is parsed by ./check_script_requirements.py -->

## Minimal
* click
* cloup
* rich
* colorama
* typing\_extensions
* requests
* tomli (if python\_version < 3.11)

## Standard
* attrs
* trio
* numpy
* Pygments
* funcparserlib
* lark


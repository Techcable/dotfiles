export MYPYPATH := "libs/python:."

lint: mypy format-check ruff

mypy:
    # Type Checking
    mypy --enable-incomplete-feature=Unpack

format: _format_py
format-check: (_format_py "--check")

FORMAT_DIRS:="src scripts libs/python fire-pit machines"
_format_py *flags:
    # format {{flags}}
    black {{flags}} {{FORMAT_DIRS}}
    isort {{flags}} --profile black {{FORMAT_DIRS}}

test: && mypy
    pytest libs/python/techcable shellrc/translate

ruff *flags:
    # ruff check {{flags}} $srcdirs
    @ruff check {{flags}} --config pyproject.toml -- "src" "machines" "libs/python"

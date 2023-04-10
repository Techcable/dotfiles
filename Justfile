export MYPYPATH := "libs/python:."

lint: mypy format-check ruff

mypy: pipenv
    # mypy (type checking)
    @pipenv run mypy

format: _format_py
format-check: (_format_py "--check")

FORMAT_DIRS:="src scripts libs/python fire-pit machines"
_format_py *flags:
    # format {{flags}}
    black {{flags}} {{FORMAT_DIRS}}
    isort {{flags}} --profile black {{FORMAT_DIRS}}

TEST_DIRS:="src libs/python"
test *flags: pipenv && mypy
    # pytest {{flags}} -- {{TEST_DIRS}}
    @pipenv run pytest {{flags}} -- {{TEST_DIRS}}

ruff *flags:
    # ruff check {{flags}} $srcdirs
    @ruff check {{flags}} --config pyproject.toml -- "src" "machines" "libs/python"

# Setup the pipenv
[private]
[unix]
pipenv:
    @pipenv sync --dev >/dev/null

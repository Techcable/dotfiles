export MYPYPATH := "libs/python:."
mypy:
    mypy

format: (_format_py "shellrc" "scripts" "libs/python")

_format_py +dirs:
    black {{dirs}}
    isort --profile black {{dirs}}

test: && mypy
    pytest libs/python/techcable shellrc/translate

pyright:
    pyright

export MYPYPATH := "libs/python:."
mypy:
    @echo "Type checking primary code"
    mypy -p shellrc.translate -p techcable
    @echo "Type checking shell configs"
    mypy shellrc/*.py

format: (_format_py "shellrc" "scripts" "libs/python")

_format_py +dirs:
    black {{dirs}}
    isort --profile black {{dirs}}

test: && mypy
    pytest libs/python/techcable shellrc/translate

format: (_format_py "shellrc" "scripts" "libs/python")


_format_py +dirs:
    black {{dirs}}
    isort --profile black {{dirs}}


check: mypy lint

# runs lints, but not type checking or tests
#
# Avoids performance penalty of `mypy`
lint: _lint && check-format

_lint:
    -ruff check src

fix: && _format fix-spelling
    @# Failure to fix should not prevent formatting
    -ruff check --fix src

mypy:
    uv run mypy src

# Check for spelling issues
spellcheck:
    # Check for obvious spelling issues
    typos

# Fix obvious spelling issues
fix-spelling:
    # Fix obvious spelling issues
    typos --write-changes

# Checks for formatting issues
check-format: && spellcheck
    @# Invoking ruff directly instead of through uv tool run saves ~12ms per command,
    @# reducing format --check src time from ~20ms to ~8ms.
    @# it reduces time for `ruff --version` from ~16ms to ~3ms.
    @# Running through `uv tool run` also frequently requires refresh of
    @# project dependencies, which can add an additional 100+ ms
    ruff format --check .
    ruff check --select I --output-format concise .

format: _format && spellcheck

_format:
    ruff format .
    ruff check --select 'I' --fix .

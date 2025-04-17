set shell := ["nu", "-c"]

SUPPORTED_VERSIONS := "['3.9' '3.10' '3.11' '3.12' '3.13']"

# Bootstrap with all supported Python versions
bootstrap:
    mkdir tmp
    uv lock --upgrade
    uv sync --all-groups
    for version in {{ SUPPORTED_VERSIONS }} { just bootstrap-with $version }

# Set up Python environment with specified Python version
bootstrap-with VERSION:
    if not (".{{ VERSION }}.venv" | path exists) { uv venv --python {{ VERSION }} --seed .{{ VERSION }}.venv }
    just python {{ VERSION }} -m pip install --upgrade uv
    just python {{ VERSION }} -m uv sync --active

# Run a specific Python interpreter
python VERSION *ARGS:
    @^".{{ VERSION }}.venv/Scripts/python.exe" -X dev {{ ARGS }}

# Run python command with the default Python version
py *ARGS:
    @uv run python -X dev {{ ARGS }}

# Run every check against source code
check: black mypy pylint test

# Check static typing
mypy:
    # Checking mypy is temporary disabled
    ## just py -m mypy src

# Static code analysis with Pylint
pylint:
    just py -m pylint src *.py

# Check code formatting
black:
    just py -m black --check src *.py

# Test with all supported Python versions
test:
    for version in {{ SUPPORTED_VERSIONS }} { just test-with $version }

# Run the tests with specified Python version
test-with VERSION:
    ^".{{ VERSION }}.venv/Scripts/pytest.exe"

# Remove compiled assets
clean:
    rm --force --recursive --verbose build dist persistedstate.egg-info

# Upgrade depedencies
upgrade-deps:
    just py -m piptools compile pyproject.toml --output-file=requirements-test.txt --upgrade --resolver=backtracking --no-annotate --extra test
    just py -m piptools compile pyproject.toml --output-file=requirements-dev.txt  --upgrade --resolver=backtracking --no-annotate --extra dev --extra perftest

# Run performance test
perftest:
    just py perftest.py

# Build the whole project, create a release
build: clean bootstrap check
    uv build

# Upload the release to PyPi
upload:
    uv upload

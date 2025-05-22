set shell := ["nu", "-c"]

# Bootstrap with all supported Python versions
bootstrap:
    mkdir tmp
    uv lock --upgrade
    uv sync --all-groups
    tox run --notest

# Run python command with the default Python version
py *ARGS:
    @uv run python -X dev {{ ARGS }}

# Run every check against source code
check: black mypy pylint test-all

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

# Test with default Python version
test:
    just py -m pytest

# Test with all supported Python versions
test-all:
    tox run

# Remove compiled assets
clean:
    rm --force --recursive --verbose build dist persistedstate.egg-info

# Run performance test
perftest:
    just py perftest.py

# Build the whole project, create a release
build: clean bootstrap check
    uv build

# Upload the release to PyPi
upload:
    uv upload

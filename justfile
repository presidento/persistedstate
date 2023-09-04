set shell := ["nu", "-c"]

DEFAULT_VERSION := "3.11"
SUPPORTED_VERSIONS := "['3.8' '3.9' '3.10' '3.11' '3.12']"

# Bootstrap with all supported Python versions
bootstrap:
    mkdir tmp
    for version in {{ SUPPORTED_VERSIONS }} { just bootstrap-with $version }
    just py -m pip install -r requirements-dev.txt

# Set up Python environment with specified Python version
bootstrap-with VERSION:
    if not (".{{ VERSION }}.venv" | path exists) { py -{{ VERSION }} -m venv .{{ VERSION }}.venv }
    just python {{ VERSION }} -m pip install --upgrade pip pip-tools build twine
    just python {{ VERSION }} -m pip install -r requirements-test.txt
    just python {{ VERSION }} -m pip install -e . --upgrade --upgrade-strategy eager

# Run a specific Python interpreter
python VERSION *ARGS:
    @^".{{ VERSION }}.venv/Scripts/python.exe" -X dev {{ ARGS }}

# Run python command with the default Python version
py *ARGS:
    @just python {{DEFAULT_VERSION }} {{ ARGS }}

# Run every check against source code
check: black mypy pylint test

# Check static typing
mypy:
    just py -m mypy src *.py

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
    just py -m piptools compile pyproject.toml --output-file=requirements-test.txt --upgrade --resolver=backtracking --extra test
    just py -m piptools compile pyproject.toml --output-file=requirements-dev.txt  --upgrade --resolver=backtracking --extra dev --extra perftest

# Run performance test
perftest:
    just py perftest.py

# Build the whole project, create a release
build: clean bootstrap check
    just py -m build

# Upload the release to PyPi
upload:
    just py -m twine upload dist/*

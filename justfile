set shell := ["nu", "-c"]

DEFAULT_VERSION := "3.11"
SUPPORTED_VERSIONS := "['3.7' '3.8' '3.9' '3.10' '3.11']"

# Bootstrap with all supported Python versions
bootstrap:
    mkdir tmp
    for version in {{ SUPPORTED_VERSIONS }} { just bootstrap-with $version }
    ^".{{ DEFAULT_VERSION }}.venv/Scripts/python.exe" -m pip install -r requirements-dev.txt

# Set up Python environment with specified Python version
bootstrap-with VERSION:
    if not (".{{ VERSION }}.venv" | path exists) { py -{{ VERSION }} -m venv .{{ VERSION }}.venv }
    ^".{{ VERSION }}.venv/Scripts/python.exe" -m pip install --upgrade pip
    ^".{{ VERSION }}.venv/Scripts/python.exe" -m pip install -r requirements-test.txt
    ^".{{ VERSION }}.venv/Scripts/python.exe" -m pip install -e . --upgrade --upgrade-strategy eager

# Run every check against source code
check-all: mypy test

# Check static typing
mypy:
    ^".{{ DEFAULT_VERSION }}.venv/Scripts/mypy.exe" src

# Test with all supported Python versions
test:
    for version in {{ SUPPORTED_VERSIONS }} { just test-with $version }

# Run the tests with specified Python version
test-with VERSION:
    ^".{{ VERSION }}.venv/Scripts/pytest.exe"

# Remove compiled assets
clean:
    rm --force --verbose build dist persistedstate.egg-info

# Upgrade depedencies
upgrade-deps:
    ^".{{ DEFAULT_VERSION }}.venv/Scripts/python.exe" -m piptools compile --output-file=requirements-test.txt --upgrade requirements-test.in
    ^".{{ DEFAULT_VERSION }}.venv/Scripts/python.exe" -m piptools compile --output-file=requirements-dev.txt --upgrade requirements-dev.in requirements-test.in

# Run performance test
perftest:
    ^".{{ DEFAULT_VERSION }}.venv/Scripts/python.exe" perftest.py

# Build the whole project, create a release
build: clean bootstrap test
    ^".{{ DEFAULT_VERSION }}.venv/Scripts/python.exe" -m build

# Upload the release to PyPi
upload:
    ^".{{ DEFAULT_VERSION }}.venv/Scripts/python.exe" -m twine upload dist/*

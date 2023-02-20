DEFAULT_VERSION := "3.11"
SUPPORTED_VERSIONS := "3.7 3.8 3.9 3.10 3.11"

set shell := ["powershell", "-nop", "-c"]

# Bootstrap with all supported Python versions
bootstrap:
    New-Item "tmp" -ItemType Directory -Force | Out-Null
    @foreach ($version in ('{{ SUPPORTED_VERSIONS }}' -split '\s+')) { just bootstrap-with "$version" }
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m pip install -r requirements-dev.txt

# Set up Python environment with specified Python version
bootstrap-with VERSION:
    If (-not (Test-Path .{{ VERSION }}.venv)) { py -{{ VERSION }} -m venv .{{ VERSION }}.venv }
    & ".{{ VERSION }}.venv\Scripts\python.exe" -m pip install --upgrade pip
    & ".{{ VERSION }}.venv\Scripts\python.exe" -m pip install -r requirements-test.txt
    & ".{{ VERSION }}.venv\Scripts\python.exe" -m pip install . --upgrade --upgrade-strategy eager

# Run every check against source code
check-all: mypy test

# Check static typing
mypy:
    just clean
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\mypy.exe" persistedstate

# Test with all supported Python versions
test:
    @foreach ($version in ('{{ SUPPORTED_VERSIONS }}' -split '\s+')) { just test-with "$version" }

# Run the tests with specified Python version
test-with VERSION:
    & ".{{ VERSION }}.venv\Scripts\pytest.exe"

# Remove compiled assets
clean:
    -Remove-Item -Recurse -Force -ErrorAction Ignore build
    -Remove-Item -Recurse -Force -ErrorAction Ignore dist
    -Remove-Item -Recurse -Force -ErrorAction Ignore persistedstate.egg-info

# Upgrade depedencies
upgrade-deps:
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m piptools compile --output-file=requirements-test.txt --upgrade requirements-test.in
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m piptools compile --output-file=requirements-dev.txt --upgrade requirements-dev.in requirements-test.in

# Run performance test
perftest:
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" perftest.py

# Build the whole project, create a release
build: clean bootstrap test
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m build

# Upload the release to PyPi
upload:
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m twine upload dist/*

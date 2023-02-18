DEFAULT_VERSION := "3.11"
SUPPORTED_VERSIONS := "3.7 3.8 3.9 3.10 3.11"

set shell := ["powershell", "-nop", "-c"]

# Bootstrap with all supported Python versions
bootstrap:
    New-Item "tmp" -ItemType Directory -Force | Out-Null
    @foreach ($version in ('{{ SUPPORTED_VERSIONS }}' -split '\s+')) { just bootstrap-with "$version" }
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m pip install mypy setuptools wheel twine pip-tools --quiet --upgrade
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m pip install -r requirements-perf.txt

# Set up Python environment with specified Python version
bootstrap-with VERSION:
    If (-not (Test-Path .{{ VERSION }}.venv)) { py -{{ VERSION }} -m venv .{{ VERSION }}.venv }
    & ".{{ VERSION }}.venv\Scripts\python.exe" -m pip install --upgrade pip
    & ".{{ VERSION }}.venv\Scripts\python.exe" -m pip install . --upgrade --upgrade-strategy eager

# Check static typing
mypy:
    just clean
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\mypy.exe" persistedstate

# Test with all supported Python versions
test: mypy
    @foreach ($version in ('{{ SUPPORTED_VERSIONS }}' -split '\s+')) { just test-with "$version" }

# Run the tests with specified Python version
test-with VERSION:
    & ".{{ VERSION }}.venv\Scripts\python.exe" .\test.py

# Remove compiled assets
clean:
    -Remove-Item -Recurse -Force -ErrorAction Ignore build
    -Remove-Item -Recurse -Force -ErrorAction Ignore dist
    -Remove-Item -Recurse -Force -ErrorAction Ignore persistedstate.egg-info

# Upgrade depedencies
upgrade-deps:
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m piptools compile --output-file=requirements-perf.txt requirements-perf.in --upgrade

# Run performance test
perftest:
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" perftest.py

# Build the whole project, create a release
build: clean bootstrap test
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" setup.py sdist bdist_wheel

# Upload the release to PyPi
upload:
    & ".{{ DEFAULT_VERSION }}.venv\Scripts\python.exe" -m twine upload dist/*

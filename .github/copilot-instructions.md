# Copilot Instructions for persistedstate

## Build & Test

This project uses **uv** as the package manager and **just** (with nushell) as the task runner.

```bash
# Install dependencies
uv sync --all-groups

# Run tests (default Python)
uv run python -m pytest

# Run a single test file or test class
uv run python -m pytest test_persistedstate.py
uv run python -m pytest test_mappedyaml.py::TestNestedDict

# Run tests across all supported Python versions (3.10–3.14)
uv run tox run

# Lint
uv run python -m pylint src *.py

# Format check
uv run python -m black --check src *.py

# All checks (format + mypy + pylint + tox)
just check
```

## Architecture

The entire library lives in a single module: `src/persistedstate/__init__.py`.

**Class hierarchy:**

- `YamlDict(MutableMapping)` — dict-like proxy that records every mutation to disk via a `FileHandler`
- `YamlList(MutableSequence)` — list-like proxy, same write-through behavior
- `MappedYaml(YamlDict)` — opens/closes the YAML file, owns the `FileHandler`
- `PersistedState(MappedYaml)` — public API; adds keyword defaults and attribute-style access (`state.foo`)

`convert()` recursively wraps plain dicts/lists into `YamlDict`/`YamlList` so nested mutations are tracked.

**Persistence model:** Write-Ahead Logging. Changes are appended as JSON journal entries after a YAML `---` separator. On `close()` (or every 2000 changes), `FileHandler.vacuum()` rewrites the file atomically with a "last valid state" safety copy inline.

**Thread safety:** All mutations acquire an `RLock` (`FileHandler.lock`), exposed as `state._thread_lock` for user-level atomic operations.

## Conventions

- **No docstrings by convention** — pylint's `missing-docstring` is globally disabled.
- **Private attributes use name-mangling** (`self.__cache`, `self.__file_handler`) — accessed from outside via explicit mangled names (e.g., `obj._YamlDict__cache`) in `CustomJsonEncoder` and YAML representers.
- **Tests live in the project root** as `test_*.py` files and use `tmp/` for state file artifacts.
- **Version scheme:** `YY.N` (two-digit year, dot, counter) — see CHANGELOG.md.
- **Python 3.10+** required; the package is typed (`py.typed` marker present).

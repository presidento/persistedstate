# 23.9

- Changing the state object is thread safe now.

# 23.8

- Remove Python 3.7 support
- Add Python 3.12 support

# 23.6

- Fix crash when the PersistedState is subclassed or constructed from another module
- Make vacuum more failure tolerant. In some edge cases it was possible for the state at beginning to overlap the state at the end.
- Internal: use `pyproject.toml` instead of `setup.py`

# 23.5

- Map the whole YAML file, so modification of nested objects are also persisted immediately

# 23.4

- In-file vacuuming

# 23.3

- Use YAML file format, not just a subset of YAML

# 23.2

- Add long description to setup.py

# 23.1

- Initial public (beta) version
- Version schema: <year:2d>.<counter>

import json
import logging
import os
import pathlib
import re
from collections.abc import MutableMapping
from typing import Any, Dict

VALID_IDENTIFIER_RE = re.compile(r"^[\w_.-]+$")

logger = logging.getLogger(__name__)


class PersistedState(MutableMapping):
    _VACUUM_ON_CHANGE = 2000

    def __init__(self, _filepath: os.PathLike, **defaults):
        self.__change_count = 0
        self.__filepath = pathlib.Path(_filepath)
        self.__filepath.touch()
        self.__file = self.__filepath.open("r+", encoding="utf-8")
        self.__cache: Dict[str, Any] = {}
        self.__load()
        if defaults:
            for key, value in defaults.items():
                if not hasattr(self, key):
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Default value set for '{key}'")
                    setattr(self, key, value)
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Default vale IS NOT set for '{key}'")

    def __load(self) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"File size on load: {self.__filepath.stat().st_size // 1024} kb"
            )
        for line in self.__file:
            key, _, value_str = line.partition(":")
            if key.startswith('"'):
                key = json.loads(key)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Loaded: '{key}'")
            self.__cache[key.strip()] = json.loads(value_str)

    def __vacuum(self) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Vacuuming")
        tmp_file = self.__filepath.with_suffix(self.__filepath.suffix + ".tmp")
        with tmp_file.open("w", encoding="utf-8") as out_file:
            for key in sorted(self.keys()):
                self.__write_line(out_file, key)
        self.__file.close()
        tmp_file.replace(self.__filepath)
        self.__file = self.__filepath.open("a", encoding="utf-8")

    def __write_line(self, file, key):
        key_str = key
        if not VALID_IDENTIFIER_RE.match(key_str):
            key_str = json.dumps(key_str).replace(":", "\\u003A")
        file.write(f"{key_str}: {json.dumps(self[key])}\n")

    def __getattr__(self, __name):
        try:
            return self[__name]
        except KeyError:
            raise AttributeError(
                f"{self.__class__} object has no attribute '{__name}'"
            ) from None

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name.startswith("_"):
            object.__setattr__(self, __name, __value)
            return
        self[__name] = __value

    def __del__(self):
        if not self.__file.closed:
            self.__vacuum()
            self.__file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.__vacuum()
        self.__file.close()

    def __getitem__(self, key):
        return self.__cache[key]

    def __setitem__(self, key, value):
        self.__cache[key] = value
        self.__write_line(self.__file, key)
        self.__change_count += 1
        if self.__change_count >= self._VACUUM_ON_CHANGE:
            self.__vacuum()
            self.__change_count = 0

    def __delitem__(self, key):
        del self.__cache[key]

    def __iter__(self):
        return iter(self.__cache)

    def __len__(self):
        return len(self.__cache)

import json
import logging
import os
import pathlib
import yaml
from collections.abc import MutableMapping
from typing import Any, Dict

logger = logging.getLogger(__name__)


class YamlDict(MutableMapping):
    _VACUUM_ON_CHANGE = 2000

    def __init__(self, _filepath: os.PathLike):
        self.__change_count = 0
        self.__filepath = pathlib.Path(_filepath)
        self.__filepath.touch()
        self.__file = self.__filepath.open("r+", encoding="utf-8")
        self.__cache: Dict[str, Any] = {}
        self.__load()

    def __load(self) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"File size on load: {self.__filepath.stat().st_size // 1024} kb"
            )
        yaml_stream = yaml.safe_load_all(self.__file)
        try:
            self.__cache.update(next(yaml_stream))
        except StopIteration:
            return
        for update in yaml_stream:
            self.__cache.update(update)

    def __vacuum(self, do_logging=True):
        if logger.isEnabledFor(logging.DEBUG) and do_logging:
            logger.debug("Vacuuming")
        tmp_file = self.__filepath.with_suffix(self.__filepath.suffix + ".tmp")
        with tmp_file.open("w", encoding="utf-8") as out_file:
            yaml.safe_dump(self.__cache, out_file, allow_unicode=True, sort_keys=True)
        self.__file.close()
        tmp_file.replace(self.__filepath)
        self.__file = self.__filepath.open("a", encoding="utf-8")

    def __write_line(self, file, key):
        file.write("\n---\n" + json.dumps({key: self[key]}, ensure_ascii=False))

    def __del__(self):
        if not self.__file.closed:
            # Assume globals are gone by now (do not log!)
            self.__vacuum(do_logging=False)
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


class PersistedState(YamlDict):
    def __init__(self, _filepath: os.PathLike, **defaults):
        super().__init__(_filepath)
        for key, value in defaults.items():
            self.setdefault(key, value)

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

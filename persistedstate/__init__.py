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
        for update in yaml.safe_load_all(self.__file):
            if type(update) == dict:
                self.__cache = update
            elif update[0] == "set":
                self.__cache[update[1]] = update[2]
            elif update[0] == "delete":
                del self.__cache[update[1]]
            else:
                raise RuntimeError("Unknow update step during recovery: " + update)

    def __vacuum(self, do_logging=True):
        if logger.isEnabledFor(logging.DEBUG) and do_logging:
            logger.debug("Vacuuming")
        yaml_str = yaml.safe_dump(self.__cache, allow_unicode=True, sort_keys=True)
        # If something goes wrong, have the last valid state at the end
        self.__file.write(yaml_str)
        self.__file.seek(0)
        self.__file.write(yaml_str)
        self.__file.flush()
        self.__file.truncate()

    def __write_change(self, *args):
        self.__file.write("\n---\n" + json.dumps([*args], ensure_ascii=False))
        self.__file.flush()

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
        self.__write_change("set", key, value)
        self.__change_count += 1
        if self.__change_count >= self._VACUUM_ON_CHANGE:
            self.__vacuum()
            self.__change_count = 0

    def __delitem__(self, key):
        self.__write_change("delete", key)
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

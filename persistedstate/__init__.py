import json
import os
import pathlib
from typing import Any, Optional


class PersistedState:
    _VACUUM_ON_CHANGE = 2000

    def __init__(self, filepath: os.PathLike, defaults: Optional[dict] = None):
        self.__change_count = 0
        self.__filepath = pathlib.Path(filepath)
        self.__filepath.touch()
        self.__file = self.__filepath.open("r+", encoding="utf-8")
        self.__load()
        if defaults:
            for key, value in defaults.items():
                if not hasattr(self, key):
                    setattr(self, key, value)

    def __load(self) -> None:
        for line in self.__file:
            key, _, value_str = line.partition(":")
            object.__setattr__(self, key.strip(), json.loads(value_str))

    def __vacuum(self) -> None:
        tmp_file = self.__filepath.with_suffix(self.__filepath.suffix + ".tmp")
        with tmp_file.open("w", encoding="utf-8") as out_file:
            for key in sorted(dir(self)):
                if key.startswith("_"):
                    continue
                self.__write_line(out_file, key)
        self.__file.close()
        tmp_file.replace(self.__filepath)
        self.__file = self.__filepath.open("a", encoding="utf-8")

    def __write_line(self, file, key):
        file.write(f"{key}: ")
        file.write(json.dumps(getattr(self, key)))
        file.write("\n")

    def __setattr__(self, __name: str, __value: Any) -> None:
        object.__setattr__(self, __name, __value)
        if __name.startswith("_"):
            return
        self.__write_line(self.__file, __name)
        self.__change_count += 1
        if self.__change_count >= self._VACUUM_ON_CHANGE:
            self.__vacuum()
            self.__change_count = 0

    def __del__(self):
        self.__vacuum()
        self.__file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.__vacuum()

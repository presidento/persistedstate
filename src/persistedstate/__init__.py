import json
import logging
import os
import pathlib
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from typing import Any, Iterator, Union

import yaml

logger = logging.getLogger(__name__)

JsonType = Union[MutableMapping, MutableSequence, str, int, float, bool, None]

SPAM_LOG = 5


class YamlDict(MutableMapping):
    def __init__(self, file_handler, path, initial_dict):
        self.__file_handler = file_handler
        self.__path = path
        self.__cache = {}
        for key, value in initial_dict.items():
            self.__cache[key] = convert(self.__file_handler, self.__path + [key], value)

    def __setitem__(self, __key: str, __value: JsonType) -> None:
        self.__file_handler.record_change("set", self.__path, __key, __value)
        return self.__cache.__setitem__(
            __key, convert(self.__file_handler, self.__path + [__key], __value)
        )

    def __delitem__(self, __key: str) -> None:
        self.__file_handler.record_change("delete", self.__path, __key)
        return self.__cache.__delitem__(__key)

    def __getitem__(self, __key: str) -> JsonType:
        return self.__cache.__getitem__(__key)

    def __iter__(self) -> Iterator[JsonType]:
        return self.__cache.__iter__()

    def __len__(self) -> int:
        return self.__cache.__len__()


class YamlList(MutableSequence):
    def __init__(self, file_handler, path, initial_list):
        self.__file_handler = file_handler
        self.__path = path
        self.__cache = []
        for item in initial_list:
            self.__cache.append(
                convert(self.__file_handler, self.__path + [len(self.__cache)], item)
            )

    def __setitem__(self, index: int, item: JsonType) -> None:
        self.__file_handler.record_change("set", self.__path, index, item)
        return self.__cache.__setitem__(
            index, convert(self.__file_handler, self.__path + [index], item)
        )

    def __delitem__(self, index: int) -> None:
        self.__file_handler.record_change("delete", self.__path, index)
        return self.__cache.__delitem__(index)

    def __getitem__(self, index: int) -> JsonType:
        return self.__cache.__getitem__(index)

    def __len__(self) -> int:
        return self.__cache.__len__()

    def insert(self, index, value):
        self.__file_handler.record_change("insert", self.__path, index, value)
        return self.__cache.insert(
            index, convert(self.__file_handler, self.__path + [index], value)
        )


def convert(file_handler, path, value: JsonType):
    if isinstance(value, Mapping):
        return YamlDict(file_handler, path, value)
    if isinstance(value, str):
        return value
    if isinstance(value, Sequence):
        return YamlList(file_handler, path, value)
    return value


def convert_to_json_like(obj):
    if isinstance(obj, str):
        return obj
    if isinstance(obj, Mapping):
        return {key: convert_to_json_like(value) for key, value in obj.items()}
    if isinstance(obj, Sequence):
        return [convert_to_json_like(item) for item in obj]
    return obj


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, YamlDict):
            return o._YamlDict__cache
        if isinstance(o, YamlList):
            return o._YamlList__cache
        return o


class FileHandler:
    _VACUUM_ON_CHANGE = 2000

    def __init__(self, parent, filepath):
        self.__parent = parent
        self.__filepath = pathlib.Path(filepath)
        self.__filepath.touch()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Open file")
        self.__file = self.__filepath.open("r+", encoding="utf-8")
        self.__change_count = 0
        self.__loading = True

    def vacuum(self, do_logging=True):
        if logger.isEnabledFor(logging.DEBUG) and do_logging:
            logger.debug("Vacuuming")
        yaml_str = yaml.safe_dump(
            convert_to_json_like(self.__parent), allow_unicode=True, sort_keys=True
        )
        self.__file.write(yaml_str)  # just padding
        self.__file.write("\n---\n### LAST VALID STATE ###\n")
        self.__file.write(yaml_str)
        self.__file.seek(0)
        self.__file.write(yaml_str)
        self.__file.write("...\n")
        self.__file.flush()
        self.__file.seek(self.__file.tell() - 5)
        self.__file.truncate()

    def record_change(self, *args):
        if self.__loading:
            return
        change_text = json.dumps([*args], cls=CustomJsonEncoder, ensure_ascii=False)
        self.__file.write("\n---\n" + change_text)
        self.__file.flush()
        self.__change_count += 1
        if logger.isEnabledFor(SPAM_LOG):
            logger.log(SPAM_LOG, "Change: " + change_text)
        if self.__change_count >= self._VACUUM_ON_CHANGE:
            self.vacuum()
            self.__change_count = 0

    @staticmethod
    def dict_representer(dumper: yaml.SafeDumper, obj: YamlDict):
        return dumper.represent_mapping("tag:yaml.org,2002:map", obj._YamlDict__cache)

    @staticmethod
    def list_representer(dumper: yaml.SafeDumper, obj: YamlList):
        return dumper.represent_sequence("tag:yaml.org,2002:seq", obj._YamlList__cache)

    def load(self):
        self.__loading = True
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"File size on load: {self.__filepath.stat().st_size // 1024} kb"
            )
        for update in yaml.safe_load_all(self.__file):
            if logger.isEnabledFor(SPAM_LOG):
                logger.log(SPAM_LOG, f"Update step: {update}")
            if update is None:
                continue
            if isinstance(update, dict):
                self.__parent.clear()
                for key, value in update.items():
                    self.__parent[key] = value
            elif update[0] == "set":
                path, key, value = update[1:]
                self.__leaf_object(path)[key] = value
            elif update[0] == "delete":
                path, key = update[1:]
                del self.__leaf_object(path)[key]
            elif update[0] == "insert":
                path, index, value = update[1:]
                self.__leaf_object(path).insert(index, value)
            else:
                raise RuntimeError(f"Unknow update step during recovery: {update}")
        self.__loading = False

    def __leaf_object(self, path):
        obj = self.__parent
        for selector in path:
            obj = obj[selector]
        return obj

    def close(self, do_logging=True):
        if self.__file.closed:
            return
        self.vacuum(do_logging)
        if logger.isEnabledFor(logging.DEBUG) and do_logging:
            logger.debug("Close file")
        self.__file.close()

    def __del__(self):
        self.close(do_logging=False)


class MappedYaml(YamlDict):
    def __init__(self, _filepath: Union[str, os.PathLike]):
        self.__file_handler = FileHandler(self, _filepath)
        super().__init__(self.__file_handler, [], {})
        self.__file_handler.load()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.__file_handler.close()

    def __del__(self):
        self.__file_handler.close(do_logging=False)


class PersistedState(MappedYaml):
    def __init__(self, _filepath: Union[str, os.PathLike], **defaults):
        super().__init__(_filepath)
        for key, value in defaults.items():
            new_value = self.setdefault(key, value)
            if logger.isEnabledFor(SPAM_LOG):
                if value == new_value:
                    verb = "IS"
                else:
                    verb = "isn't"
                logger.log(SPAM_LOG, f"Default value {verb} set: {key} = {value}")

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
            if logger.isEnabledFor(SPAM_LOG):
                logger.log(SPAM_LOG, f"Setting Python attribute {__name} = {__value}")
            return
        self[__name] = __value

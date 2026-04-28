import json
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from typing import Iterator, Union

JsonType = Union[MutableMapping, MutableSequence, str, int, float, bool, None]


class YamlDict(MutableMapping):
    def __init__(self, file_handler, path, initial_dict):
        self.__file_handler = file_handler
        self.__path = path
        self.__cache = {}
        self.__lock = file_handler.lock
        for key, value in initial_dict.items():
            self.__cache[key] = convert(self.__file_handler, self.__path + [key], value)

    def __setitem__(self, __key: str, __value: JsonType) -> None:
        with self.__lock:
            self.__file_handler.record_change("set", self.__path, __key, __value)
            return self.__cache.__setitem__(
                __key, convert(self.__file_handler, self.__path + [__key], __value)
            )

    def __delitem__(self, __key: str) -> None:
        with self.__lock:
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
        self.__lock = file_handler.lock
        for item in initial_list:
            self.__cache.append(
                convert(self.__file_handler, self.__path + [len(self.__cache)], item)
            )

    def __setitem__(self, index: int, item: JsonType) -> None:
        if isinstance(index, slice):
            raise TypeError("YamlList does not support slice assignment")
        with self.__lock:
            self.__file_handler.record_change("set", self.__path, index, item)
            return self.__cache.__setitem__(
                index, convert(self.__file_handler, self.__path + [index], item)
            )

    def __delitem__(self, index: int) -> None:
        if isinstance(index, slice):
            raise TypeError("YamlList does not support slice deletion")
        with self.__lock:
            self.__file_handler.record_change("delete", self.__path, index)
            self.__cache.__delitem__(index)
            depth = len(self.__path)
            for i in range(index, len(self.__cache)):
                _update_path_index(self.__cache[i], depth, -1)

    def __getitem__(self, index: int) -> JsonType:
        if isinstance(index, slice):
            raise TypeError("YamlList does not support slice access")
        return self.__cache.__getitem__(index)

    def __len__(self) -> int:
        return self.__cache.__len__()

    def insert(self, index, value):
        with self.__lock:
            depth = len(self.__path)
            for i in range(index, len(self.__cache)):
                _update_path_index(self.__cache[i], depth, 1)
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


def _update_path_index(obj, depth, delta):
    if isinstance(obj, YamlDict):
        obj._YamlDict__path[depth] += delta
        for child in obj._YamlDict__cache.values():
            _update_path_index(child, depth, delta)
    elif isinstance(obj, YamlList):
        obj._YamlList__path[depth] += delta
        for child in obj._YamlList__cache:
            _update_path_index(child, depth, delta)


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

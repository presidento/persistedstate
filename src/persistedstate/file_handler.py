import json
import logging
import pathlib
from threading import RLock

import yaml

from persistedstate.types import (
    CustomJsonEncoder,
    YamlDict,
    YamlList,
    convert_to_json_like,
)

logger = logging.getLogger(__name__)

SPAM_LOG = 5


class FileHandler:
    _VACUUM_ON_CHANGE = 2000

    def __init__(self, parent, filepath):
        self.__parent = parent
        self.__filepath = pathlib.Path(filepath)
        self.__filepath.touch()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Open file {self.__filepath}")
        self.__file = self.__filepath.open("r+", encoding="utf-8")
        self.__change_count = 0
        self.__loading = True
        self.lock = RLock()

    def vacuum(self, do_logging=True):
        with self.lock:
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
        with self.lock:
            if self.__change_count >= self._VACUUM_ON_CHANGE:
                self.vacuum()
                self.__change_count = 0
            change_text = json.dumps([*args], cls=CustomJsonEncoder, ensure_ascii=False)
            self.__file.write("\n---\n" + change_text)
            self.__file.flush()
            self.__change_count += 1
            if logger.isEnabledFor(SPAM_LOG):
                logger.log(SPAM_LOG, f"Change ({self.__change_count}): {change_text}")

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
                raise RuntimeError(f"Unknown update step during recovery: {update}")
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

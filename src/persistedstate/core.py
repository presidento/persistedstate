import logging
import os
from typing import Any, Union

from persistedstate.file_handler import FileHandler, SPAM_LOG
from persistedstate.types import YamlDict

logger = logging.getLogger(__name__)


class MappedYaml(YamlDict):
    def __init__(self, _filepath: Union[str, os.PathLike]):
        self.__file_handler = FileHandler(self, _filepath)
        self._thread_lock = self.__file_handler.lock
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

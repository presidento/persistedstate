import json
import pathlib
import shelve
import time

import pickledb
from diskcache import Cache
from lmdbm import Lmdb
from sqlitedict import SqliteDict

from persistedstate import PersistedState

COUNT_TO = 10_000
TMP_FOLDER = pathlib.Path("tmp")


class BaseTest:
    def do_the_count(self):
        pass

    def perftest(self):
        start = time.perf_counter()
        self.do_the_count()
        end = time.perf_counter()
        test_name = self.__class__.__name__.replace("Test", "")
        print(f"{test_name:<15s} {end-start:6.3f} sec")


class PersistedStateTest(BaseTest):
    def __init__(self) -> None:
        file = TMP_FOLDER / "persisted.state"
        file.unlink(missing_ok=True)
        self.state = PersistedState(file)

    def do_the_count(self):
        self.state.counter = 0
        for _ in range(COUNT_TO):
            self.state.counter += 1


class BaseDictTest(BaseTest):
    def do_the_count(self):
        self.dict["counter"] = 0
        for _ in range(COUNT_TO):
            self.dict["counter"] += 1


class ShelveTest(BaseDictTest):
    def __init__(self) -> None:
        self.dict = shelve.open(TMP_FOLDER / "shelve.dat")


class SqliteDictTest(BaseDictTest):
    def __init__(self) -> None:
        self.dict = SqliteDict(TMP_FOLDER / "sqlitedict.sqlite")


class DiskCacheTest(BaseDictTest):
    def __init__(self) -> None:
        self.dict = Cache(TMP_FOLDER / "diskcache")


class PickleDbTest(BaseTest):
    def __init__(self) -> None:
        self.db = pickledb.load(TMP_FOLDER / "pickle.db", auto_dump=True)

    def do_the_count(self):
        self.db.set("counter", 0)
        for _ in range(COUNT_TO):
            self.db.set("counter", self.db.get("counter") + 1)


class JsonLmdb(Lmdb):
    def _pre_value(self, value):
        return json.dumps(value).encode("utf-8")

    def _post_value(self, value):
        return json.loads(value.decode("utf-8"))


class LmdbTest(BaseDictTest):
    def __init__(self):
        self.dict = JsonLmdb.open((TMP_FOLDER / "lmdb").as_posix(), "c")


print(f"Counting to {COUNT_TO}")
PersistedStateTest().perftest()
DiskCacheTest().perftest()
SqliteDictTest().perftest()
ShelveTest().perftest()
PickleDbTest().perftest()
LmdbTest().perftest()

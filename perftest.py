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
TMP_FOLDER = pathlib.Path("tmp/perftest")
STATE = PersistedState("tmp/perftest.state")
ITERATIONS = 5

TMP_FOLDER.mkdir(parents=True, exist_ok=True)


class BaseTest:
    def do_the_count(self):
        pass

    def perftest(self, iteration):
        test_name = self.__class__.__name__.replace("Test", "")
        STATE.setdefault(test_name, [])
        if len(STATE[test_name]) > iteration:
            duration = STATE[test_name][iteration]
        else:
            start = time.perf_counter()
            self.do_the_count()
            end = time.perf_counter()
            duration = end - start
            STATE[test_name].append(duration)
        print(f"{test_name:<15s} {duration:6.3f} sec")

    def print_best_result(self):
        test_name = self.__class__.__name__.replace("Test", "")
        duration = min(STATE[test_name])
        print(f"{test_name:<15s} {duration:6.3f} sec")


class PersistedStateTest(BaseTest):
    def do_the_count(self):
        file = TMP_FOLDER / "persisted.state"
        file.unlink(missing_ok=True)
        with PersistedState(file) as state:
            state.counter = 0
            for _ in range(COUNT_TO):
                state.counter += 1


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


TEST_CLASSES = [
    PersistedStateTest,
    DiskCacheTest,
    SqliteDictTest,
    PickleDbTest,
    LmdbTest,
    ShelveTest,
]


def main():
    STATE.pop("PersistedState", None)
    print(f"Counting to {COUNT_TO}")
    for iteration in range(ITERATIONS):
        print(f"\nIteration #{iteration}\n")
        for klass in TEST_CLASSES:
            klass().perftest(iteration)
    print(f"\nBest results:\n")
    for klass in TEST_CLASSES:
        klass().print_best_result()


main()

import pathlib
import textwrap
from abc import ABC, abstractmethod

from persistedstate import PersistedState

TMP_PATH = pathlib.Path("tmp")
BACKUP_PATH = TMP_PATH / "unittest-backup"
BACKUP_PATH.mkdir(exist_ok=True, parents=True)


class Base(ABC):
    file1 = pathlib.Path("tmp/test1.state")
    file2 = pathlib.Path("tmp/test2.state")
    input_data = ""

    def test_change(self):
        self.file1.write_text(
            textwrap.dedent(self.input_data).strip(), encoding="utf-8"
        )
        with PersistedState(self.file1) as state:
            self.change(state)
            changed_data = self.file1.read_text(encoding="utf-8")
            (BACKUP_PATH / self.__class__.__name__).with_suffix(".yaml").write_text(
                changed_data, encoding="utf-8"
            )
            self.file2.write_text(changed_data, encoding="utf-8")
        with PersistedState(self.file2) as state:
            self.assertions(state)

    @abstractmethod
    def change(self, state):
        pass

    @abstractmethod
    def assertions(self, state):
        pass


class TestBasicTestWithoutChange(Base):
    input_data = """
        string: Peach
        num: 42
        bool: true
        dict:
            array:
            - 793
        """

    def change(self, state):
        pass

    def assertions(self, state):
        assert state.string == "Peach"
        assert state.num == 42
        assert state.dict["array"][0] == 793
        assert state.bool


class TestTopLevelDict(Base):
    input_data = """
        a: a
        b: b
        c: c
        """

    def change(self, state):
        state.a = "AA"
        del state["b"]

    def assertions(self, state):
        assert state.a == "AA"
        assert "b" not in state
        assert state.c == "c"


class TestNestedDict(Base):
    input_data = """
        top:
            a: a
            b: b
            c: c
        """

    def change(self, state):
        state.top["a"] = "AA"
        del state.top["b"]

    def assertions(self, state):
        assert state.top["a"] == "AA"
        assert "b" not in state.top
        assert state.top["c"] == "c"


class TestList(Base):
    input_data = """
        list:
        - 20
        - 30
        - 40
        """

    def change(self, state):
        del state.list[1]
        state.list.insert(0, 10)
        state.list.append(50)

    def assertions(self, state):
        assert [10, 20, 40, 50] == list(state.list)


class TestMultiChange(Base):
    def change(self, state):
        state.list = [{"a": "A"}, 1, 2]
        state.list[0]["b"] = "B"
        del state.list[0]["a"]
        state.list[2] += 10
        state.list.append({"c": "C"})
        state.list[3]["c"] = "CC"

    def assertions(self, state):
        assert dict(state.list[0]) == {"b": "B"}
        assert state.list[2] == 12
        assert state.list[3]["c"] == "CC"

import pathlib
from persistedstate import PersistedState
from abc import ABC, abstractmethod
import textwrap

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

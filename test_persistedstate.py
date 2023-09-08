import pathlib
import textwrap

from persistedstate import PersistedState


class TestAttributes:
    def setup_method(self) -> None:
        self.filepath = pathlib.Path("tmp/test.state")
        self.filepath.unlink(missing_ok=True)

    def test_default_values(self):
        with PersistedState(self.filepath, num=42, string="Hello") as state:
            assert state.num == 42
            assert state.string == "Hello"

    def test_persisting_attributes(self):
        with PersistedState(self.filepath, string="Hello") as state:
            state.bool = True
            state.string = "Ahoi"
        with PersistedState(self.filepath) as state:
            assert state.bool
            assert state.string == "Ahoi"
        expected_state = textwrap.dedent(
            """
            bool: true
            string: Ahoi
            """
        ).strip()
        assert expected_state == self.filepath.read_text(encoding="utf-8").strip()

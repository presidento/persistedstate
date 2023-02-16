import pathlib
import textwrap
import unittest

from persistedstate import PersistedState


class TestAttributes(unittest.TestCase):
    def setUp(self) -> None:
        self.filepath = pathlib.Path("tmp/test.state")
        self.filepath.unlink(missing_ok=True)
        return super().setUp()

    def test_default_values(self):
        state = PersistedState(self.filepath, num=42, string="Hello")
        assert state.num == 42
        assert state.string == "Hello"

    def test_persistance(self):
        self.filepath.write_text(
            textwrap.dedent(
                """
                num: 55
                string: "Ahoi"
                """
            ).strip()
        )
        state = PersistedState(self.filepath, num=42, string="Hello")
        assert state.num == 55
        assert state.string == "Ahoi"

    def test_new_attribute(self):
        with PersistedState(self.filepath) as state:
            state.bool = True
        assert "bool: true" == self.filepath.read_text().strip()


if __name__ == "__main__":
    unittest.main()

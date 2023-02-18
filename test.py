import pathlib
import textwrap
import unittest

from persistedstate import PersistedState


class TestAttributes(unittest.TestCase):
    def setUp(self) -> None:
        self.filepath = pathlib.Path("tmp/test.state")
        try:
            self.filepath.unlink()
        except FileNotFoundError:
            # missing_ok parameter is not available in Python 3.7
            pass
        return super().setUp()

    def test_default_values(self):
        state = PersistedState(self.filepath, num=42, string="Hello")
        assert state.num == 42
        assert state.string == "Hello"

    def test_persisted_attributes_instead_of_default_value(self):
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
        assert expected_state == self.filepath.read_text().strip()

    def test_dict_interface(self):
        with PersistedState(self.filepath) as state:
            for i in range(10):
                state[f"Item #{i}"] = i
        with PersistedState(self.filepath) as state:
            for i in range(10):
                assert state[f"Item #{i}"] == i


if __name__ == "__main__":
    unittest.main()

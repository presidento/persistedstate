import pathlib
import textwrap
import unittest

from persistedstate import PersistedState, MappedYaml


class TestYamlDict(unittest.TestCase):
    def setUp(self):
        self.filepath = pathlib.Path("tmp/test.yaml")
        try:
            self.filepath.unlink()
        except FileNotFoundError:
            # missing_ok parameter is not available in Python 3.7
            pass
        return super().setUp()

    def test_keys_are_sorted(self):
        with MappedYaml(self.filepath) as mydict:
            mydict["d"] = 10
            mydict["a"] = 1
            mydict["f"] = 100
        expected = textwrap.dedent(
            """
            a: 1
            d: 10
            f: 100
            """
        )
        assert self.filepath.read_text(encoding="utf-8").strip() == expected.strip()

    def test_journal(self):
        tmp_file = self.filepath.with_name("test2.yaml")
        with MappedYaml(self.filepath) as mydict:
            mydict["a"] = 1
            mydict["b"] = 2
            mydict["c"] = 3

        with MappedYaml(self.filepath) as mydict:
            mydict["a"] = 10
            del mydict["b"]
            mydict["d"] = 4
            data_with_journal = self.filepath.read_text(encoding="utf-8")
            tmp_file.write_text(data_with_journal, encoding="utf-8")
            expected = textwrap.dedent(
                """
                a: 1
                b: 2
                c: 3

                ---
                ["set", "a", 10]
                ---
                ["delete", "b"]
                ---
                ["set", "d", 4]
                """
            ).strip()
            assert data_with_journal == expected
            assert dict(mydict) == dict(MappedYaml(tmp_file))

    def test_dict_interface(self):
        with PersistedState(self.filepath) as state:
            for i in range(10):
                state[f"Item #{i}"] = i
        with PersistedState(self.filepath) as state:
            for i in range(10):
                assert state[f"Item #{i}"] == i


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


if __name__ == "__main__":
    unittest.main()

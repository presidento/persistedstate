import scripthelper

from persistedstate import PersistedState

scripthelper.bootstrap()

state = PersistedState("tmp/loggertest.state", string="Hello")
state.string = "Ahoi"
state.num = 42
state.bool = True
state.list = []
state.list.append({"a": "A"})
state.list[0]["a"] = "AA"
state.close()

import logging
from persistedstate import PersistedState

logging.basicConfig(level=logging.DEBUG)

with PersistedState("tmp/loggertest.state", string="Hello") as state:
    state.string = "Ahoi"
    state.num = 42
    state.bool = True

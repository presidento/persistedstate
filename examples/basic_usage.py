#!/usr/bin/env python3
from persistedstate import PersistedState

STATE = PersistedState("tmp/example.state", last_id=0)

for current_id in range(STATE.last_id + 1, 100_001):
    print(f"Processing #{current_id}")
    STATE.last_id = current_id

print("Processing DONE.")

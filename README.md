# PersistedState

Simple and fast solution for persisting small states:

```python
from persistedstate import PersistedState

STATE = PersistedState("example.state", last_id=0)

for current_id in range(STATE.last_id + 1, 100_001):
    print(f"Processing item #{current_id}")
    STATE.last_id = current_id

print("Processing DONE.")
```

You can interrupt this script, and next time it will continue from the first unprocessed item.

## Editable state file

The use case is persisting small amount of data which can be edited easily with a text editor.
The database is an UTF-8 encoded text file, using a subset of YAML, so it can be highlighted.

## Failure tolerance

It uses Write-Ahead-Logging and atomic vacuum, so there will be no data loss.

## Performance

For its use case it outperforms existing key-value store modules.
For example incrementing a counter (see [perftest.py](perftest.py)):

```python
state.counter = 0
for _ in range(COUNT_TO):
    state.counter += 1
```

Counting to 10,000:

```
PersistedState   0.062 sec
DiskCache        1.331 sec
SqliteDict       4.298 sec
Shelve           4.492 sec
PickleDb        10.728 sec
Lmdb            16.980 sec
```

The example seems to be silly, but this is very close to the use case it was developed for. For complex data structures or big amount of data I suggest using other libraries, like [DiskCache](https://grantjenks.com/docs/diskcache/). (The rule of thumb is when your state file is too big to be edited easily in your favorite text editor, you may think about using another key-value store library.)
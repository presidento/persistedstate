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
As another example see [perftest.py](perftest.py).

## Mapped YAML state file

The use case is persisting small amount of data which can be edited easily with a text editor.
The database is an UTF-8 encoded YAML file, so it can be highlighted and edited manually if needed.
(It also uses YAML stream file format for journal.)
The YAML file is fully mapped to Python objects, so every change is synchronized to disk immediately. E.g. you can do this:

```python
STATE = PersistedState("state.yaml", processed_items=[])
STATE.setdefault("key", {})
STATE["key"].setdefault("nested", 2)

STATE.processed_items.append("<some item>")
STATE["key"]["nested"] += 1
```

## Failure tolerance

It uses Write-Ahead-Logging and atomic vacuum, so there will be no data loss.

## Thread safe

Changing the state is thread safe. You also can use the `._thread_lock` attribute to make atomic changes:


```python
def atomic_increment():
    with STATE._thread_lock:
        STATE.counter += 1
```

## Performance

For its use case it outperforms existing key-value store modules.
For example incrementing a counter (for the details see [perftest.py](perftest.py)):

```python
state.counter = 0
for _ in range(COUNT_TO):
    state.counter += 1
```

Counting to 10,000 (using Windows and Python 3.11):

```
PersistedState   0.193 sec
DiskCache        1.222 sec
SqliteDict       3.089 sec
PickleDb         8.251 sec
Lmdb            14.944 sec
Shelve          39.771 sec
```

The example seems to be silly, but this is very close to the use case it was developed for. For complex data structures or big amount of data I suggest using other libraries, like [DiskCache](https://grantjenks.com/docs/diskcache/). (The rule of thumb is when your state file is too big to be edited easily in your favorite text editor, you may think about using another key-value store library.)
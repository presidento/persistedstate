import pathlib
import concurrent.futures

from src.persistedstate import PersistedState

NUM_OF_THREADS = 128

class TestThreads:
    def setup_method(self):
        self.filepath = pathlib.Path("tmp/threads.state")
        self.filepath.unlink(missing_ok=True)
        self.state = None

    def test_thread_usage(self):
        self.open_state()
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_OF_THREADS) as executor:
            futures = (executor.submit(self.threaded_function) for _ in range(NUM_OF_THREADS))
            concurrent.futures.wait(futures)
        self.close_state()

        self.open_state()
        assert self.state.index == NUM_OF_THREADS
        assert list(self.state.list) == [i + 1 for i in range(NUM_OF_THREADS)]
        self.close_state()

    def open_state(self):
        self.state = PersistedState(self.filepath, index=0, list=[])

    def close_state(self):
        self.state.close()

    def threaded_function(self):
        with self.state._thread_lock:
            self.state.index += 1
            self.state.list.append(self.state.index)


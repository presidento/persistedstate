import concurrent.futures
import pathlib
import shutil
import threading

from src.persistedstate import PersistedState

NUM_OF_THREADS = 100
STEPS_OF_EACH_THREAD = 10
STATE_FILE = pathlib.Path("tmp/threads.state")
TEMP_FILE = STATE_FILE.with_suffix(".tmp")


class TestThreads:
    def setup_method(self):
        self.filepath = STATE_FILE
        self.filepath.unlink(missing_ok=True)
        self.state = None

    def test_thread_usage(self):
        self.open_state()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=NUM_OF_THREADS
        ) as executor:
            futures = [
                executor.submit(self.threaded_function) for _ in range(NUM_OF_THREADS)
            ]
            concurrent.futures.wait(futures)
        shutil.copy(STATE_FILE, TEMP_FILE)
        self.close_state()
        STATE_FILE.unlink()
        shutil.copy(TEMP_FILE, STATE_FILE)

        self.open_state()
        assert len(self.state.list) == NUM_OF_THREADS * STEPS_OF_EACH_THREAD
        self.close_state()

    def open_state(self):
        self.state = PersistedState(self.filepath, index=0, list=[])

    def close_state(self):
        self.state.close()

    def threaded_function(self):
        for _ in range(STEPS_OF_EACH_THREAD):
            self.state.list.append(threading.get_ident())

"""
@Date    : 2026/5/15 16:28
@Author  : Chiang
@Desc    : None
"""
import threading


class TmpIdLock:
    """
    自带id的lock，用于临时并发lock, 用后即删
    """

    _id2lock = {}
    _id2count = {}
    _i2l_lock = threading.Lock()

    def __init__(self, ident: str):
        self._ident = ident
        self._lock: threading.Lock | None = None

    def __enter__(self) -> bool:
        with self._i2l_lock:
            self._lock = self._id2lock.setdefault(self._ident, threading.Lock())
            self._id2count[self._ident] = self._id2count.get(self._ident, 0) + 1
        return self._lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._lock.release()
        with self._i2l_lock:
            count = self._id2count.get(self._ident, 1)
            if count <= 1:
                self._id2lock.pop(self._ident, None)
                self._id2count.pop(self._ident, None)
            else:
                self._id2count[self._ident] -= 1

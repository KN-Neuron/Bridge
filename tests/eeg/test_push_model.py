import threading
import time

import numpy as np
import pytest

from bridge.eeg.core import EEGDevice
from bridge.eeg.core.device_data import DeviceData


class _StubDevice(EEGDevice):

    def __init__(self, n_chunks: int = 5, chunk_shape: tuple = (4, 10)) -> None:
        super().__init__()
        self._n_chunks = n_chunks
        self._chunk_shape = chunk_shape
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def stream(self):
        for i in range(self._n_chunks):
            if not self._connected:
                return
            yield np.full(self._chunk_shape, float(i), dtype=np.float64)

    def get_device_data(self) -> DeviceData:
        return DeviceData(name="StubDevice", sample_rate=250)


def test_subscribe_registers_callback():
    device = _StubDevice()
    cb = lambda chunk: None  # noqa: E731
    device.subscribe(cb)
    assert cb in device._subscribers


def test_start_pushes_chunks_to_subscriber():
    device = _StubDevice(n_chunks=4)
    received: list[np.ndarray] = []

    device.connect()
    device.subscribe(received.append)
    device.start()
    device._push_thread.join(timeout=2)

    assert len(received) == 4
    assert received[0].shape == (4, 10)


def test_stop_joins_thread():
    device = _StubDevice(n_chunks=10)
    device.connect()
    device.subscribe(lambda _: time.sleep(0.01))
    device.start()
    device.stop()

    assert device._push_thread is None
    assert not device._connected


def test_multiple_subscribers_all_receive():
    device = _StubDevice(n_chunks=3)
    received_a: list = []
    received_b: list = []

    device.connect()
    device.subscribe(received_a.append)
    device.subscribe(received_b.append)
    device.start()
    device._push_thread.join(timeout=2)

    assert len(received_a) == 3
    assert len(received_b) == 3


def test_subscriber_exception_does_not_crash_push_loop():
    device = _StubDevice(n_chunks=3)
    received: list = []

    def bad_cb(chunk):
        raise RuntimeError("boom")

    device.connect()
    device.subscribe(bad_cb)
    device.subscribe(received.append)
    device.start()
    device._push_thread.join(timeout=2)

    assert len(received) == 3


def test_chunk_values_are_correct():
    device = _StubDevice(n_chunks=3)
    received: list[np.ndarray] = []

    device.connect()
    device.subscribe(received.append)
    device.start()
    device._push_thread.join(timeout=2)

    for i, chunk in enumerate(received):
        np.testing.assert_array_equal(chunk, np.full((4, 10), float(i)))

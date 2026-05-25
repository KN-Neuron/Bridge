import threading
import time
from pathlib import Path

import numpy as np
import pytest

from bridge.eeg.core import EEGDevice
from bridge.eeg.core.device_data import DeviceData
from bridge.eeg.fif import FifDevice, FifRecorder

pytest.importorskip("mne", reason="mne not installed — skipping FIF tests")

_CAP = {0: "C3", 1: "C4", 2: "Cz", 3: "Fz"}
_N_CH = len(_CAP)
_CHUNK = 25
_SFREQ = 250.0


class _FakeDevice(EEGDevice):

    def __init__(self, n_chunks: int = 8) -> None:
        super().__init__()
        self._n = n_chunks
        self._on = False

    def connect(self) -> None:
        self._on = True

    def disconnect(self) -> None:
        self._on = False

    def stream(self):
        rng = np.random.default_rng(0)
        for _ in range(self._n):
            yield rng.standard_normal((_N_CH, _CHUNK))

    def get_device_data(self) -> DeviceData:
        return DeviceData(name="FakeDevice", sample_rate=int(_SFREQ))


def _record(tmp_path: Path, n_chunks: int = 8) -> Path:
    fif_path = tmp_path / "session.fif"
    dev = _FakeDevice(n_chunks=n_chunks)
    dev.connect()
    rec = FifRecorder(dev, str(fif_path), cap=_CAP, sfreq=_SFREQ)
    chunks = []
    def _run():
        for c in rec.stream():
            chunks.append(c)
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(0.5)
    dev.disconnect()
    t.join(timeout=2)
    rec.save()
    return fif_path


def test_fif_recorder_creates_file(tmp_path):
    path = _record(tmp_path)
    assert path.exists()
    assert path.stat().st_size > 0


def test_fif_device_connects_without_error(tmp_path):
    path = _record(tmp_path)
    device = FifDevice(str(path), chunk_size=_CHUNK)
    device.connect()
    device.disconnect()


def test_fif_device_chunk_shape(tmp_path):
    path = _record(tmp_path)
    device = FifDevice(str(path), chunk_size=_CHUNK)
    device.connect()
    chunks = list(device.stream())
    device.disconnect()
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.shape == (_N_CH, _CHUNK)


def test_fif_device_chunk_dtype(tmp_path):
    path = _record(tmp_path)
    device = FifDevice(str(path), chunk_size=_CHUNK)
    device.connect()
    chunks = list(device.stream())
    device.disconnect()
    assert chunks[0].dtype == np.float64


def test_fif_device_missing_file_raises():
    device = FifDevice("nonexistent.fif", chunk_size=_CHUNK)
    with pytest.raises(FileNotFoundError):
        device.connect()


def test_fif_roundtrip_data_matches(tmp_path):
    fif_path = tmp_path / "rt.fif"
    rng = np.random.default_rng(42)
    original = rng.standard_normal((_N_CH, _CHUNK * 4))

    import mne
    import warnings
    info = mne.create_info(list(_CAP.values()), sfreq=_SFREQ, ch_types="eeg")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mne.io.RawArray(original, info, verbose=False).save(str(fif_path), overwrite=True, verbose=False)

    device = FifDevice(str(fif_path), chunk_size=_CHUNK)
    device.connect()
    chunks = list(device.stream())
    device.disconnect()

    recovered = np.concatenate(chunks, axis=1)
    np.testing.assert_allclose(recovered, original[:, : recovered.shape[1]], atol=1e-10)


def test_fif_device_get_device_data(tmp_path):
    path = _record(tmp_path)
    device = FifDevice(str(path), chunk_size=_CHUNK)
    device.connect()
    info = device.get_device_data()
    device.disconnect()
    assert info.sample_rate == int(_SFREQ)

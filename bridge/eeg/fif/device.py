import time
import warnings
from logging import Logger, getLogger
from pathlib import Path
from typing import Final, Generator

import numpy as np

from ..core import DeviceData, EEGArray, EEGDevice


class FifDevice(EEGDevice):
    def __init__(self, file_path: str, chunk_size: int = 25, logger: Logger | None = None) -> None:
        try:
            import mne  # noqa: F401
        except ImportError as e:
            raise ImportError("FIF support requires mne: pip install 'neuron-bridge[fif]'") from e

        super().__init__(logger or getLogger(__name__))
        self._path: Final[Path] = Path(file_path)
        self._chunk_size: Final[int] = chunk_size
        self._data: np.ndarray | None = None
        self._sfreq: float = 250.0
        self._is_connected: bool = False

    def connect(self) -> None:
        import mne

        if not self._path.exists():
            raise FileNotFoundError(f"FIF file not found: {self._path}")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            raw = mne.io.read_raw_fif(str(self._path), preload=True, verbose=False)
        self._sfreq = float(raw.info["sfreq"])
        self._data = raw.get_data()
        self._is_connected = True
        if self._data is not None:
            data: np.ndarray = self._data
            self._logger.info("FifDevice connected: %d ch × %d samples @ %.0f Hz", *data.shape, self._sfreq)

    def disconnect(self) -> None:
        self._is_connected = False

    def stream(self) -> Generator[EEGArray, None, None]:
        if not self._is_connected or self._data is None:
            raise RuntimeError("FifDevice not connected.")

        n_samples = self._data.shape[1]
        interval: Final[float] = self._chunk_size / self._sfreq
        start_perf: Final[float] = time.perf_counter()

        for count, start in enumerate(range(0, n_samples - self._chunk_size + 1, self._chunk_size), start=1):
            if not self._is_connected:
                break

            target: float = start_perf + count * interval
            while time.perf_counter() < target:
                diff = target - time.perf_counter()
                if diff > 0.002:
                    time.sleep(diff - 0.001)

            yield self._data[:, start : start + self._chunk_size].astype(np.float64)

    def get_device_data(self) -> DeviceData:
        return DeviceData(name=self._path.name, manufacturer="FifSim", sample_rate=int(self._sfreq))

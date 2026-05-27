import time
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Final, Generator

import numpy as np

from ..core import DeviceData, EEGArray, EEGDevice


class FileDevice(EEGDevice):
    """Emulator odtwarzający sesje z plików binarnych .npz."""

    def __init__(
        self, file_path: str, sfreq: float = 250.0, chunk_size: int = 25, logger: Logger | None = None
    ) -> None:
        super().__init__(logger or getLogger(__name__))
        self._path: Final[Path] = Path(file_path)
        self._sfreq: Final[float] = sfreq
        self._chunk_size: Final[int] = chunk_size
        self._data: np.ndarray[Any, Any] | None = None
        self._is_connected: bool = False

    def connect(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(f"Binary file not found: {self._path}")

        with np.load(self._path) as loader:
            self._data = loader["data"]

        self._is_connected = True
        if self._data is None or self._data.size == 0:
            raise ValueError(f"No data found in file: {self._path}")

        self._logger.info("FileDevice connected. Data shape: %s", self._data.shape)

    def disconnect(self) -> None:
        self._is_connected = False

    def stream(self) -> Generator[EEGArray, None, None]:
        if not self._is_connected or self._data is None:
            raise RuntimeError("FileDevice not connected.")

        n_samples = self._data.shape[1]
        interval: Final[float] = self._chunk_size / self._sfreq
        start_perf: Final[float] = time.perf_counter()

        for count, start in enumerate(range(0, n_samples - self._chunk_size + 1, self._chunk_size), start=1):
            if not self._is_connected:
                break

            target: float = start_perf + (count * interval)
            while time.perf_counter() < target:
                diff = target - time.perf_counter()
                if diff > 0.002:
                    time.sleep(diff - 0.001)

            yield self._data[:, start : start + self._chunk_size].astype(np.float64)

    def get_device_data(self) -> DeviceData:
        return DeviceData(name=self._path.name, manufacturer="BinarySim", sample_rate=int(self._sfreq))

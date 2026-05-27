import time
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Final, Generator

import numpy as np

from .core import EEGArray, EEGDevice
from .core.device_data import RecordingFrame


class EEGRecorder:
    """Rejestrator EEG wykorzystujący wysokowydajny format binarny NumPy."""

    def __init__(
        self,
        device: EEGDevice,
        filename: str,
        logger: Logger | None = None,
        autosave: bool = True,
        connect_device: bool = True,
    ) -> None:
        self._logger: Final[Logger] = logger or getLogger(__name__)
        self._device: Final[EEGDevice] = device
        self._filename: Final[str] = filename
        self._autosave: Final[bool] = autosave
        self._connect_device: Final[bool] = connect_device
        self._frames: list[RecordingFrame] = []

    def __enter__(self) -> "EEGRecorder":
        if self._connect_device:
            self._device.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._autosave:
            self.save()
        if self._connect_device:
            self._device.disconnect()

    def stream(self) -> Generator[EEGArray, None, None]:
        """Strumieniuje dane i buforuje je w pamięci jako RecordingFrame."""
        for chunk in self._device.stream():
            self._frames.append(RecordingFrame(timestamp=time.time(), data=chunk))
            yield chunk

    def save(self) -> None:
        """Zapisuje dane do skompresowanego pliku binarnego NumPy (.npz)."""
        if not self._frames:
            self._logger.warning("No data to save.")
            return

        try:
            output_dir: Final[Path] = Path("recordings")
            output_dir.mkdir(exist_ok=True)
            file_path: Final[Path] = output_dir / self._filename

            timestamps: Final[np.ndarray[Any, Any]] = np.array([f.timestamp for f in self._frames])
            data_blocks: Final[np.ndarray[Any, Any]] = np.concatenate([f.data for f in self._frames], axis=1)

            np.savez_compressed(file_path, timestamps=timestamps, data=data_blocks)

            self._logger.info("Saved session to binary file: %s", file_path)

        except (OSError, IOError) as e:
            self._logger.error("Failed to save recording to disk: %s", e)
            raise

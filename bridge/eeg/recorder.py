import time
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Final, Generator

import numpy as np

from .core import EEGArray, EEGDevice
from .core.device_data import RecordingFrame


def save_recording(
    data: np.ndarray[Any, Any],
    path: str | Path,
    sfreq: float | None = None,
    ch_names: list[str] | None = None,
    logger: Logger | None = None,
) -> None:
    _log = logger or getLogger(__name__)
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    arrays: dict[str, Any] = {
        "timestamps": np.array([time.time()]),
        "data": data,
    }
    if sfreq is not None:
        arrays["sfreq"] = np.float64(sfreq)
    if ch_names is not None:
        arrays["ch_names"] = np.array(ch_names, dtype=str)

    np.savez_compressed(dest, **arrays)
    _log.info("Saved recording to %s", dest)


class EEGRecorder:
    """Rejestrator EEG wykorzystujący wysokowydajny format binarny NumPy."""

    def __init__(
        self,
        device: EEGDevice,
        filename: str,
        output_dir: str | Path = "recordings",
        sfreq: float | None = None,
        ch_names: list[str] | None = None,
        logger: Logger | None = None,
        autosave: bool = True,
        connect_device: bool = True,
    ) -> None:
        self._logger: Final[Logger] = logger or getLogger(__name__)
        self._device: Final[EEGDevice] = device
        self._filename: Final[str] = filename
        self._output_dir: Final[Path] = Path(output_dir)
        self._sfreq: float | None = sfreq
        self._ch_names: list[str] | None = ch_names
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
            self._output_dir.mkdir(parents=True, exist_ok=True)
            file_path: Final[Path] = self._output_dir / self._filename

            timestamps: Final[np.ndarray[Any, Any]] = np.array([f.timestamp for f in self._frames])
            data_blocks: Final[np.ndarray[Any, Any]] = np.concatenate([f.data for f in self._frames], axis=1)

            arrays: dict[str, Any] = {"timestamps": timestamps, "data": data_blocks}
            if self._sfreq is not None:
                arrays["sfreq"] = np.float64(self._sfreq)
            if self._ch_names is not None:
                arrays["ch_names"] = np.array(self._ch_names, dtype=str)

            np.savez_compressed(file_path, **arrays)

            self._logger.info("Saved session to binary file: %s", file_path)

        except (OSError, IOError) as e:
            self._logger.error("Failed to save recording to disk: %s", e)
            raise

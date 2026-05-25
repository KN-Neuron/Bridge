import time
import warnings
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Final, Generator

import numpy as np

from ..core import EEGArray, EEGDevice
from ..core.device_data import RecordingFrame


class FifRecorder:
    """Records an EEG stream and saves it as an MNE FIF file."""

    def __init__(
        self,
        device: EEGDevice,
        filename: str,
        cap: dict[int, str],
        sfreq: float = 250.0,
        logger: Logger | None = None,
        autosave: bool = True,
    ) -> None:
        try:
            import mne  # noqa: F401
        except ImportError as e:
            raise ImportError("FIF support requires mne: pip install 'neuron-bridge[fif]'") from e

        self._logger: Final[Logger] = logger or getLogger(__name__)
        self._device: Final[EEGDevice] = device
        self._filename: Final[str] = filename
        self._cap: Final[dict[int, str]] = cap
        self._sfreq: Final[float] = sfreq
        self._autosave: Final[bool] = autosave
        self._frames: list[RecordingFrame] = []

    def __enter__(self) -> "FifRecorder":
        self._device.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._autosave:
            self.save()
        self._device.disconnect()

    def stream(self) -> Generator[EEGArray, None, None]:
        for chunk in self._device.stream():
            self._frames.append(RecordingFrame(timestamp=time.time(), data=chunk))
            yield chunk

    def save(self) -> None:
        import mne

        if not self._frames:
            self._logger.warning("No data to save.")
            return

        try:
            output_dir: Final[Path] = Path("recordings")
            output_dir.mkdir(exist_ok=True)
            file_path: Final[Path] = output_dir / self._filename

            data = np.concatenate([f.data for f in self._frames], axis=1)
            ch_names = [self._cap[i] for i in sorted(self._cap)]
            info = mne.create_info(ch_names=ch_names, sfreq=self._sfreq, ch_types="eeg")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                mne.io.RawArray(data, info, verbose=False).save(str(file_path), overwrite=True, verbose=False)

            self._logger.info("Saved session to FIF: %s", file_path)

        except (OSError, IOError) as e:
            self._logger.error("Failed to save FIF recording: %s", e)
            raise

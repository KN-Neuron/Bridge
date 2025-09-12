from logging import Logger, getLogger
from types import TracebackType
from typing import Iterable

from .config import DEVICE_CLASSES
from .core import DeviceData, EEGArray, EEGDevice


class EEGConnector:
    def __init__(
        self,
        device_classes: Iterable[type[EEGDevice]] = DEVICE_CLASSES,
        output_file: str | None = None,
        logger: Logger = getLogger(__name__),
    ):
        self._device_classes: Iterable[type[EEGDevice]] = device_classes
        self._eeg_device: EEGDevice | None = None
        self._output_file: str | None = output_file
        self._logger: Logger = logger

    def _ensure_connected(self) -> EEGDevice:
        if self._eeg_device is None:
            raise RuntimeError("No device is currently connected.")
        return self._eeg_device

    def connect(self) -> None:
        if self._eeg_device is not None:
            raise RuntimeError("A device is already connected.")
        if not self._device_classes:
            raise ValueError("No device classes provided for connection.")

        for device_class in self._device_classes:
            try:
                device = device_class()
                device.connect()
                self._eeg_device = device
                self._logger.info(f"Successfully connected using {device_class.__name__}.")
                return
            except Exception as e:
                self._logger.warning(f"Failed to connect using {device_class.__name__}: {e}")

        raise RuntimeError("Failed to connect to any available device.")

    def disconnect(self) -> None:
        device = self._ensure_connected()
        device.disconnect()
        self._eeg_device = None

    def get_impedance(self, duration: float) -> list[float]:
        device = self._ensure_connected()
        return device.get_impedance(duration=duration)

    def get_output(self, duration: float) -> EEGArray:
        device = self._ensure_connected()
        return device.get_output(output_file=self._output_file, duration=duration)

    def get_device_data(self) -> DeviceData | None:
        device = self._ensure_connected()
        return device.get_device_data()

    def __enter__(self) -> "EEGConnector":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.disconnect()
        return None

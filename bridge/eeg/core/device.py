from abc import ABC, abstractmethod
from logging import Logger, getLogger
from types import TracebackType

from .device_data import DeviceData
from .typing import EEGArray


class EEGDevice(ABC):
    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger or getLogger(__name__)
        self._logger.debug(f"{self.__class__.__name__} initialized.")

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def get_output(self, duration: float, output_file: str | None = None) -> EEGArray:
        pass

    def get_impedance(self, duration: float) -> list[float]:
        raise NotImplementedError(f"Impedance measurement not implemented for this class {self.__class__.__name__}.")

    @abstractmethod
    def get_device_data(self) -> DeviceData | None:
        pass

    def __enter__(self) -> "EEGDevice":
        self._logger.debug("Entering context manager...")
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._logger.debug("Exiting context manager...")
        self.disconnect()
        return None

import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from logging import Logger, getLogger
from types import TracebackType
from typing import Generator

from .device_data import DeviceData
from .typing import EEGArray


class EEGDevice(ABC):
    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger or getLogger(__name__)
        self._logger.debug(f"{self.__class__.__name__} initialized.")
        self._subscribers: list[Callable[[EEGArray], None]] = []
        self._push_thread: threading.Thread | None = None

    def subscribe(self, callback: Callable[[EEGArray], None]) -> None:
        self._subscribers.append(callback)

    def start(self) -> None:
        self._push_thread = threading.Thread(target=self._push_loop, daemon=True)
        self._push_thread.start()

    def stop(self) -> None:
        self.disconnect()
        if self._push_thread is not None:
            self._push_thread.join(timeout=5)
            self._push_thread = None

    def _push_loop(self) -> None:
        for chunk in self.stream():
            for cb in list(self._subscribers):
                try:
                    cb(chunk)
                except Exception:
                    self._logger.exception("Subscriber %r raised", cb)

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    def get_output(self, duration: float, output_file: str | None = None) -> EEGArray:
        raise NotImplementedError(f"Output retrieval not implemented for this class {self.__class__.__name__}.")

    def get_impedance(self, duration: float) -> list[float]:
        raise NotImplementedError(f"Impedance measurement not implemented for this class {self.__class__.__name__}.")

    def stream(self) -> Generator[EEGArray, None, None]:
        raise NotImplementedError(f"Streaming not implemented for this class {self.__class__.__name__}.")

    @abstractmethod
    def get_device_data(self) -> DeviceData:
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

import multiprocessing
import time
from logging import Logger, getLogger

from brainaccess import core
from brainaccess.core.eeg_manager import EEGManager
from brainaccess.utils import acquisition
from brainaccess.utils.acquisition import EEG

from ..core import DeviceData, EEGArray, EEGDevice
from .cap_factory import get_cap_from_model, get_cap_from_name
from .config import (
    BRAINACCESS_MANUFACTURER,
    DATA_COLLECTION_TIME,
    DEFAULT_BLUETOOTH_ADAPTER,
    DEFAULT_DEVICE_PORT,
    IMPEDANCE_MEASUREMENT_TIME,
)

connection_lock = multiprocessing.Lock()


class BrainaccessDevice(EEGDevice):
    def __init__(self, logger: Logger | None = None) -> None:
        self._eeg: EEG = acquisition.EEG()
        self._manager: EEGManager | None = None
        self._cap: dict[int, str] | None = None
        self._mac_address: str | None = None
        self._device_name: str | None = None

        super().__init__(logger or getLogger(__name__))

    def _ensure_connected(self) -> None:
        if not self._manager:
            self._logger.error("Device is not connected.")
            raise RuntimeError("Device is not connected.")

    # IM-032
    def _connect(self, device_name: str, cap: dict[int, str]) -> None:
        if not self._manager:
            self._manager = EEGManager()
        self._manager.__enter__()
        try:
            self._eeg.setup(self._manager, device_name=device_name, cap=cap)
            self._electrodes = list(cap.values())
            self._logger.info("Connection successful.")
        except Exception:
            self._manager.__exit__(None, None, None)
            raise

        self._logger.info("Connection successful.")

    # IM-032
    def _get_device_model(self, port: int) -> str:
        status = self._manager.connect(port)  # type: ignore[union-attr]

        if status != 0:
            self._manager.destroy()  # type: ignore[union-attr]
            self._manager = None
            raise ConnectionError(f"Connection failed with status {status}.")

        self._logger.debug("Valid connection status.")

        info = self._manager.get_device_info()  # type: ignore[union-attr]
        self._manager.disconnect()  # type: ignore[union-attr]

        device_model = info.device_model.name

        return device_model  # type: ignore[no-any-return]

    # IM-032
    def connect(
        self,
        bluetooth_adapter: int = DEFAULT_BLUETOOTH_ADAPTER,
        port: int = DEFAULT_DEVICE_PORT,
    ) -> None:
        self._manager = EEGManager()

        with connection_lock:
            self._logger.debug("Scanning for eeg...")
            core.scan(adapter_index=bluetooth_adapter)
            count = core.get_device_count()
            self._logger.info(f"Found {count} eeg.")

            if count == 0:
                raise ConnectionError("Can't connect. No device found.")

            self._logger.debug(f"Attempting to connect to the device on port {port}...")

            if port >= count:
                raise ConnectionError(f"Can't connect on port {port}, found {count} eeg.")

            self._device_name = core.get_device_name(port) or "Unknown Device"
            self._mac_address = core.get_device_address(port)
            self._cap = get_cap_from_name(self._device_name)

            if not self._cap:
                model = self._get_device_model(port)
                self._cap = get_cap_from_model(model)

            try:
                self._connect(self._device_name, self._cap)
                return
            except Exception as e:
                self._logger.exception(e)

    # IM-032
    def disconnect(self) -> None:
        self._ensure_connected()
        self._logger.debug("Disconnecting the device...")
        if self._manager:
            self._manager.disconnect()
            self._manager.__exit__(None, None, None)
            # self._manager.destroy()
            self._manager = None
        self._eeg.close()

        self._logger.info("Device disconnected successfully.")

    # IM-032
    def get_impedance(self, duration: float = IMPEDANCE_MEASUREMENT_TIME) -> list[float]:
        self._ensure_connected()
        self._logger.info(f"Starting impedance measurement for {duration} seconds...")
        self._eeg.start_impedance_measurement()

        self._logger.debug(f"Waiting for {duration} seconds...")
        time.sleep(duration)

        self._logger.debug("Calculating impedance...")
        impedance = self._eeg.calc_impedances(duration)
        self._logger.debug("Stopping the measurement...")
        self._eeg.stop_impedance_measurement()
        self._logger.info(f"Impedance measurement completed: {impedance}")

        return impedance  # type: ignore[no-any-return]

    # IM-032
    def get_output(self, duration: float = DATA_COLLECTION_TIME, output_file: str | None = None) -> EEGArray:
        self._ensure_connected()
        self._logger.info(f"Starting data acquisition for {duration} seconds...")
        self._eeg.start_acquisition()

        time.sleep(duration)

        self._eeg.get_mne()
        self._eeg.stop_acquisition()

        if output_file:
            self._logger.info(f"Saving output data to file: {output_file}")
            self._eeg.data.save(output_file)

        raw_data = self._eeg.data.mne_raw.get_data()
        self._logger.info("Data acquisition completed.")
        return raw_data  # type: ignore[no-any-return]

    def get_device_data(self) -> DeviceData | None:
        self._ensure_connected()
        try:
            return DeviceData(
                name=self._device_name,
                mac_address=self._mac_address,
                manufacturer=BRAINACCESS_MANUFACTURER,
                electrodes_num=len(self._cap) if self._cap else None,
                sample_rate=self._manager.get_sample_frequency() if self._manager else None,
            )
        except Exception as e:
            self._logger.exception(f"Failed to fetch device data for device {self.__class__.__name__}: {e}")
            return None

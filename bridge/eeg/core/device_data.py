from dataclasses import dataclass

from bridge.eeg.core.typing import EEGArray


@dataclass(frozen=True, slots=True, kw_only=True)
class DeviceData:
    mac_address: str | None = None
    name: str | None = None
    manufacturer: str | None = None
    electrodes_num: int | None = None
    sample_rate: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordingFrame:
    timestamp: float
    data: EEGArray

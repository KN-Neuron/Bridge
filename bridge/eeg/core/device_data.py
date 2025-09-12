from dataclasses import dataclass


@dataclass
class DeviceData:
    mac_address: str | None = None
    name: str | None = None
    manufacturer: str | None = None
    electrodes_num: int | None = None
    sample_rate: int | None = None

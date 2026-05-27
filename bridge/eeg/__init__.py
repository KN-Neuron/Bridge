from .config import close, init
from .connector import EEGConnector
from .core import DeviceData, EEGArray, EEGDevice
from .fif import FifDevice, FifRecorder

__all__ = [
    "DeviceData",
    "EEGDevice",
    "EEGArray",
    "init",
    "close",
    "EEGConnector",
    "FifDevice",
    "FifRecorder",
]

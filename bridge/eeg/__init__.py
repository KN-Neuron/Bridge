from .config import close, init
from .connector import EEGConnector
from .core import DeviceData, EEGArray, EEGDevice

__all__ = [
    "DeviceData",
    "EEGDevice",
    "EEGArray",
    "init",
    "close",
    "EEGConnector",
]

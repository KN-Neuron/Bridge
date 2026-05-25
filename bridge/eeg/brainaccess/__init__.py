from .cap_factory import DEVICE_TO_CAP, get_cap_from_model, get_cap_from_name

__all__ = [
    "DEVICE_TO_CAP",
    "get_cap_from_model",
    "get_cap_from_name",
]

try:
    from .device import BrainaccessDevice
    __all__ = [*__all__, "BrainaccessDevice"]
except ImportError:
    pass

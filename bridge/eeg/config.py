from logging import getLogger
from typing import Callable

from .core import EEGDevice

logger = getLogger(__name__)

device_classes_list: list[type[EEGDevice]] = []
init_functions: list[Callable[[], None]] = []
close_functions: list[Callable[[], None]] = []

try:
    from brainaccess import core

    from .brainaccess import BrainaccessDevice

    device_classes_list.append(BrainaccessDevice)
    init_functions.append(core.init)
    close_functions.append(core.close)
    logger.debug("Successfully registered BrainAccess device support.")
except ImportError:
    logger.warning("Could not load BrainAccess support.")

DEVICE_CLASSES = tuple(device_classes_list)
if not DEVICE_CLASSES:
    logger.warning("No EEG device classes registered.")


def init() -> None:
    """Initializes all registered device SDKs."""
    for func in init_functions:
        func()


def close() -> None:
    """Closes all registered device SDKs."""
    for func in close_functions:
        func()

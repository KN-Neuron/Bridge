from unittest.mock import MagicMock

import pytest

from bridge.eeg.connector import EEGConnector
from bridge.eeg.core import EEGDevice


class MockSuccessfulDevice(EEGDevice):
    def connect(self) -> None:
        print(f"{self.__class__.__name__} connected.")

    def disconnect(self) -> None:
        pass

    def get_output(self, duration: float, output_file: str | None = None):
        return [1, 2, 3]

    def get_device_data(self):
        return "SuccessData"


class MockFailingDevice(EEGDevice):
    def connect(self) -> None:
        raise ConnectionError("Failed to connect")

    def disconnect(self) -> None:
        pass

    def get_output(self, duration: float, output_file: str | None = None):
        pass

    def get_device_data(self):
        pass


def test_connector_no_device_classes():
    """Test that EEGConnector raises ValueError if no device classes are provided."""
    connector = EEGConnector(device_classes=[])
    with pytest.raises(ValueError, match="No device classes provided"):
        connector.connect()


def test_connector_connects_to_first_successful_device():
    """Test that the connector tries devices in order and connects to the first available one."""
    device_classes = [MockFailingDevice, MockSuccessfulDevice]
    connector = EEGConnector(device_classes=device_classes)
    connector.connect()
    assert isinstance(connector._eeg_device, MockSuccessfulDevice)


def test_connector_fails_if_all_devices_fail():
    """Test that the connector raises RuntimeError if all connections fail."""
    device_classes = [MockFailingDevice, MockFailingDevice]
    connector = EEGConnector(device_classes=device_classes)
    with pytest.raises(RuntimeError, match="Failed to connect to any available device."):
        connector.connect()


def test_connector_methods_delegate_to_device():
    """Verify that connector methods call the underlying device's methods."""
    mock_device = MockSuccessfulDevice()
    mock_device.get_output = MagicMock(return_value=[1, 2, 3])
    mock_device.get_device_data = MagicMock(return_value="SuccessData")

    mock_device_class = MagicMock(spec=MockSuccessfulDevice)
    mock_device_class.return_value = mock_device
    mock_device_class.__name__ = "MockSuccessfulDevice"

    connector = EEGConnector(device_classes=[mock_device_class])
    connector.connect()

    assert connector.get_output(duration=5.0) == [1, 2, 3]
    mock_device.get_output.assert_called_once_with(output_file=None, duration=5.0)

    assert connector.get_device_data() == "SuccessData"
    mock_device.get_device_data.assert_called_once()


def test_connector_raises_error_if_not_connected():
    """Test that methods raise an error if called before connecting."""
    connector = EEGConnector(device_classes=[MockSuccessfulDevice])
    with pytest.raises(RuntimeError, match="No device is currently connected"):
        connector.get_output(duration=1.0)


def test_connector_as_context_manager():
    """Test the __enter__ and __exit__ methods for resource management."""
    mock_device = MockSuccessfulDevice()
    mock_device.connect = MagicMock()
    mock_device.disconnect = MagicMock()

    mock_device_class = MagicMock(spec=MockSuccessfulDevice)
    mock_device_class.return_value = mock_device
    mock_device_class.__name__ = "MockSuccessfulDevice"

    with EEGConnector(device_classes=[mock_device_class]) as connector:
        assert connector._eeg_device is not None
        mock_device.connect.assert_called_once()
        mock_device.disconnect.assert_not_called()

    mock_device.disconnect.assert_called_once()
    assert connector._eeg_device is None

from unittest.mock import MagicMock, patch

import pytest

brainaccess = pytest.importorskip("brainaccess")

from bridge.eeg.brainaccess.device import BrainaccessDevice  # noqa: E402


@pytest.fixture
def mock_brainaccess_sdk(monkeypatch):
    """Mocks the brainaccess SDK components used by BrainaccessDevice."""
    mock_core = MagicMock()
    monkeypatch.setattr("bridge.eeg.brainaccess.device.core", mock_core)

    mock_acquisition = MagicMock()
    mock_eeg_instance = MagicMock()
    mock_acquisition.EEG.return_value = mock_eeg_instance
    monkeypatch.setattr("bridge.eeg.brainaccess.device.acquisition", mock_acquisition)

    mock_eeg_manager_instance = MagicMock()
    monkeypatch.setattr("bridge.eeg.brainaccess.device.EEGManager", lambda: mock_eeg_manager_instance)

    mock_core.EEGManager.return_value = mock_eeg_manager_instance

    return mock_core


def test_brainaccess_device_initialization(mock_brainaccess_sdk):
    """Verify that the device initializes without error."""
    device = BrainaccessDevice()
    assert device is not None
    assert isinstance(device._eeg, MagicMock)


def test_connect_no_devices_found(mock_brainaccess_sdk):
    """Test connection failure when no devices are found."""
    mock_brainaccess_sdk.get_device_count.return_value = 0
    device = BrainaccessDevice()
    with pytest.raises(ConnectionError, match="Can't connect. No device found."):
        device.connect()
    mock_brainaccess_sdk.scan.assert_called_once()


def test_connect_successful(mock_brainaccess_sdk):
    """Test a successful connection flow."""
    mock_brainaccess_sdk.get_device_count.return_value = 1
    mock_brainaccess_sdk.get_device_name.return_value = "BRAINACCESS-MAXI-1234"
    mock_brainaccess_sdk.get_device_address.return_value = "00:11:22:33:44:55"

    manager_instance = mock_brainaccess_sdk.EEGManager()

    device = BrainaccessDevice()
    device.connect(port=0)

    mock_brainaccess_sdk.scan.assert_called_once()
    mock_brainaccess_sdk.get_device_name.assert_called_with(0)
    manager_instance.__enter__.assert_called_once()
    assert device._device_name == "BRAINACCESS-MAXI-1234"
    assert device._mac_address == "00:11:22:33:44:55"
    assert "P8" in device._cap.values()  # Check if MAXI cap was loaded


def test_get_output_calls_sdk_correctly(mock_brainaccess_sdk):
    """Verify that get_output calls the underlying SDK methods in order."""
    # Setup a connected device
    device = BrainaccessDevice()
    device._manager = mock_brainaccess_sdk.EEGManager()
    # device._eeg is already a MagicMock due to the fixture
    eeg_mock = device._eeg

    with patch("time.sleep") as mock_sleep:
        device.get_output(duration=5.0)

    eeg_mock.start_acquisition.assert_called_once()
    mock_sleep.assert_called_once_with(5.0)
    eeg_mock.get_mne.assert_called_once()
    eeg_mock.stop_acquisition.assert_called_once()
    eeg_mock.data.mne_raw.get_data.assert_called_once()


def test_connection_lock_is_used(mock_brainaccess_sdk):
    """Verify that the multiprocessing lock is acquired during connection."""
    mock_brainaccess_sdk.get_device_count.return_value = 0
    device = BrainaccessDevice()

    with patch("bridge.eeg.brainaccess.device.connection_lock") as mock_lock:
        with pytest.raises(ConnectionError):
            device.connect()
        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()

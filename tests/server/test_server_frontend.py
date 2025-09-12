import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from bridge.eeg.core import DeviceData
from bridge.server.handlers.frontend import FrontendHandler


@pytest.fixture
def mock_eeg_connector(monkeypatch):
    """Fixture to mock the EEGConnector."""
    mock = MagicMock()
    monkeypatch.setattr("bridge.server.handlers.frontend.EEGConnector", lambda: mock)
    return mock


@pytest.fixture
def mock_websocket():
    """Fixture to mock the WebSocketServerProtocol."""
    websocket = AsyncMock()
    websocket.send = AsyncMock()
    return websocket


@pytest.fixture
def handler(mock_eeg_connector):
    """Fixture to create a FrontendHandler instance."""
    mock_backend_handler = MagicMock()
    # By depending on mock_eeg_connector, we ensure the patch is active
    # before FrontendHandler is instantiated, so it gets the mocked connector.
    return FrontendHandler(backend_handler=mock_backend_handler)


@pytest.mark.asyncio
async def test_connect_device_success(handler, mock_eeg_connector, mock_websocket):
    """Test successful device connection request."""
    message = json.dumps({"request": "connect_device"})
    mock_websocket.__aiter__ = lambda self: self
    mock_websocket.__anext__ = AsyncMock(side_effect=[message, StopAsyncIteration])

    await handler.request_handler(mock_websocket)

    mock_eeg_connector.connect.assert_called_once()
    response = json.loads(mock_websocket.send.call_args[0][0])
    assert response == {"result": "Device connected successfully."}
    assert handler._is_eeg_connected is True


@pytest.mark.asyncio
async def test_connect_device_failure(handler, mock_eeg_connector, mock_websocket):
    """Test failed device connection request."""
    mock_eeg_connector.connect.side_effect = RuntimeError("Connection Failed")
    message = json.dumps({"request": "connect_device"})
    mock_websocket.__aiter__ = lambda self: self
    mock_websocket.__anext__ = AsyncMock(side_effect=[message, StopAsyncIteration])

    await handler.request_handler(mock_websocket)

    response = json.loads(mock_websocket.send.call_args[0][0])
    assert response == {"error": "Connection failed: Connection Failed"}
    assert handler._is_eeg_connected is False


@pytest.mark.asyncio
async def test_get_device_info_not_connected(handler, mock_websocket):
    """Test get_device_info request when no device is connected."""
    message = json.dumps({"request": "get_device_info"})
    mock_websocket.__aiter__ = lambda self: self
    mock_websocket.__anext__ = AsyncMock(side_effect=[message, StopAsyncIteration])

    await handler.request_handler(mock_websocket)

    response = json.loads(mock_websocket.send.call_args[0][0])
    assert response == {"error": "Device not connected. Please send 'connect_device' request first."}


@pytest.mark.asyncio
async def test_get_device_info_success(handler, mock_eeg_connector, mock_websocket):
    """Test successful get_device_info request."""
    handler._is_eeg_connected = True
    device_data = DeviceData(name="TestDevice", sample_rate=250)
    mock_eeg_connector.get_device_data.return_value = device_data

    message = json.dumps({"request": "get_device_info"})
    mock_websocket.__aiter__ = lambda self: self
    mock_websocket.__anext__ = AsyncMock(side_effect=[message, StopAsyncIteration])

    await handler.request_handler(mock_websocket)

    mock_eeg_connector.get_device_data.assert_called_once()
    response = json.loads(mock_websocket.send.call_args[0][0])
    assert response["result"]["name"] == "TestDevice"
    assert response["result"]["sample_rate"] == 250


@pytest.mark.asyncio
async def test_unknown_request(handler, mock_websocket):
    """Test that an unknown request receives an error."""
    message = json.dumps({"request": "unknown_action"})
    mock_websocket.__aiter__ = lambda self: self
    mock_websocket.__anext__ = AsyncMock(side_effect=[message, StopAsyncIteration])

    await handler.request_handler(mock_websocket)

    response = json.loads(mock_websocket.send.call_args[0][0])
    assert response == {"error": "Unknown request"}

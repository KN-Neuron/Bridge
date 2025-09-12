import asyncio
import dataclasses
import json
import logging
from typing import Any

from websockets.server import WebSocketServerProtocol

from bridge.eeg.connector import EEGConnector
from bridge.server.handlers.backend import BackendHandler


class FrontendHandler:
    def __init__(self, backend_handler: BackendHandler) -> None:
        self._backend_handler: BackendHandler = backend_handler
        self._eeg_connector: EEGConnector = EEGConnector()
        self._is_eeg_connected: bool = False

    async def request_handler(self, websocket: WebSocketServerProtocol) -> None:
        actions_map = {
            "connect_device": self.connect_device,
            "disconnect_device": self.disconnect_device,
            "get_device_info": self.get_device_info,
            "send_data": self.send_data,
        }

        async for message in websocket:
            try:
                data = json.loads(message)
                request = data.get("request")

                if request not in actions_map:
                    await websocket.send(json.dumps({"error": "Unknown request"}))
                    continue

                method = actions_map[request]
                result = await method()
                await websocket.send(json.dumps(result))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON format"}))
            except Exception as e:
                await websocket.send(json.dumps({"error": str(e)}))

    async def connect_device(self) -> dict[str, Any]:
        if self._is_eeg_connected:
            return {"result": "Device already connected."}
        try:
            await asyncio.to_thread(self._eeg_connector.connect)
            self._is_eeg_connected = True
            logging.info("EEG device connected.")
            return {"result": "Device connected successfully."}
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return {"error": f"Connection failed: {e}"}

    async def disconnect_device(self) -> dict[str, Any]:
        if not self._is_eeg_connected:
            return {"result": "Device is not connected."}
        try:
            await asyncio.to_thread(self._eeg_connector.disconnect)
            self._is_eeg_connected = False
            logging.info("EEG device disconnected.")
            return {"result": "Device disconnected successfully."}
        except Exception as e:
            logging.error(f"Disconnection error: {e}")
            return {"error": f"Disconnection error: {e}"}

    async def get_device_info(self) -> dict[str, Any]:
        if not self._is_eeg_connected:
            return {"error": "Device not connected. Please send 'connect_device' request first."}
        try:
            device_data = await asyncio.to_thread(self._eeg_connector.get_device_data)
            if device_data:
                return {"result": dataclasses.asdict(device_data)}
            return {"error": "Could not retrieve device info."}
        except Exception as e:
            logging.error(f"Failed to get device info: {e}")
            return {"error": f"Failed to get device info: {e}"}

    async def send_data(self) -> dict[str, Any]:
        if not self._is_eeg_connected:
            return {"error": "Device not connected. Please send 'connect_device' request first."}
        try:
            data = await asyncio.to_thread(self._eeg_connector.get_output, duration=10.0)
            return {"result": data.tolist()}
        except Exception as e:
            logging.error(f"Failed to get data: {e}")
            return {"error": f"Failed to get data: {e}"}

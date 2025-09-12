import asyncio
import json
from json import JSONDecodeError
from typing import Any, cast

import websockets
from websockets import ConnectionClosed, ConnectionClosedError
from websockets.client import WebSocketClientProtocol


class BackendHandler:
    def __init__(self, backend_uri: str) -> None:
        self._uri: str = backend_uri
        self._connection: WebSocketClientProtocol | None = None

    async def connect(self) -> None:
        self._connection = await websockets.connect(self._uri)

    async def get_preprocessing_params(self) -> dict[str, Any]:
        if self._connection is None:
            await self.connect()
        assert self._connection is not None

        try:
            await self._connection.send(json.dumps({"request": "get_preprocessing_params"}))
            response = await self._connection.recv()
            return cast(dict[str, Any], json.loads(response))
        except (ConnectionClosed, ConnectionClosedError, ConnectionRefusedError) as e:
            raise ConnectionError("Connection to backend was lost or refused") from e
        except JSONDecodeError as e:
            raise JSONDecodeError("Invalid response format from backend", e.doc, e.pos) from e
        except asyncio.TimeoutError as e:
            raise TimeoutError("Timeout while waiting for response from backend") from e
        except Exception as e:
            raise Exception(f"Unexpected Error: {e}") from e

    async def get_public_key(self) -> dict[str, str]:
        assert self._connection is not None, "Connection must be established before getting the public key."

        try:
            await self._connection.send(json.dumps({"request": "get_public_key"}))
            response = await self._connection.recv()
            return cast(dict[str, str], json.loads(response))
        except (ConnectionClosed, ConnectionClosedError, ConnectionRefusedError) as e:
            raise ConnectionError("Connection to backend was lost or refused") from e
        except JSONDecodeError as e:
            raise JSONDecodeError("Invalid response format from backend", e.doc, e.pos) from e
        except asyncio.TimeoutError as e:
            raise TimeoutError("Timeout while waiting for response from backend") from e
        except Exception as e:
            raise Exception(str(e)) from e

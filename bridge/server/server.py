import logging
import ssl

import websockets

from .handlers import BackendHandler, FrontendHandler


class BridgeServer:
    def __init__(self, ip: str, port: int, ssl_cert: str, ssl_key: str, backend_uri: str) -> None:
        self._ip: str = ip
        self._port: int = port
        self._backend_handler: BackendHandler = BackendHandler(backend_uri)
        self._frontend_handler: FrontendHandler = FrontendHandler(self._backend_handler)

    @staticmethod
    def _create_ssl_context(ssl_cert: str, ssl_key: str) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=ssl_cert, keyfile=ssl_key)
        return context

    async def start(self) -> None:
        server = await websockets.serve(self._frontend_handler.request_handler, self._ip, self._port)
        await self._backend_handler.connect()
        logging.info(f"Server started at ws://{self._ip}:{self._port}")
        await server.wait_closed()

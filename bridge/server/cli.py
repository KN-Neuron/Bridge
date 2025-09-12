import argparse
import asyncio
import logging
import sys

from .. import eeg
from .server import BridgeServer


def run_server_cli() -> None:
    """Parses command-line arguments and runs the Bridge server."""
    parser = argparse.ArgumentParser(description="Neuroguard Bridge Server")
    parser.add_argument("--host", type=str, default="localhost", help="Host IP to bind the server to")
    parser.add_argument("--port", type=int, default=50050, help="Port to bind the server to")
    parser.add_argument(
        "--backend-uri",
        type=str,
        default="ws://localhost:8765",
        help="WebSocket URI of the backend server",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose DEBUG logging")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        eeg.init()
        server = BridgeServer(
            ip=args.host,
            port=args.port,
            ssl_cert="",
            ssl_key="",
            backend_uri=args.backend_uri,
        )
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logging.info("Server is shutting down.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    finally:
        eeg.close()
        logging.info("Bridge resources have been released.")

import json
import logging
import socket
from datetime import datetime

from db.con import Machine

# Global socket variable that persists between function calls
recv_sock = None


async def listen_for_boards() -> None:
    """
    Listen for UDP broadcasts from boards on the network.
    This function is designed to be called regularly from a FastAPI scheduler.
    """
    global recv_sock
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Listening for board announcements...")

    # The UDP port used for discovery
    DISCOVERY_PORT = 37020

    # Create socket only if it doesn't exist
    if recv_sock is None:
        try:
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            recv_sock.bind(("0.0.0.0", DISCOVERY_PORT))
            recv_sock.setblocking(False)
            logger.info(f"Created socket listening on UDP port {DISCOVERY_PORT}")
        except Exception as e:
            logger.error(f"Failed to set up socket: {e}")
            return

    # Process incoming announcements
    try:
        while True:
            try:
                data, addr = recv_sock.recvfrom(1024)
            except BlockingIOError:
                # No more data available
                break

            try:
                msg = json.loads(data.decode("utf-8"))
                logger.debug(f"Received message: {msg}")
            except json.JSONDecodeError:
                continue

            # Check for required fields
            if "name" in msg and "version" in msg and "ip" in msg:
                title = msg["name"]
                version = msg["version"]
                ip = msg["ip"]  # Use IP from the message

                logger.info(f"Board announcement from {title} at {ip} (version: {version})")

                # Update database
                await Machine.upsert(
                    id=ip, ip=ip, title=title, version=version, last_seen=datetime.now()
                )
            else:
                logger.debug("Received incomplete announcement, missing required fields")

    except Exception as e:
        logger.error(f"Error while listening for boards: {e}")

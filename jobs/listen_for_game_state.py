import json
import logging
import socket

# Global socket variable that persists between function calls
recv_sock = None


async def listen_for_game_state() -> None:
    """
    Listen for UDP broadcasts from boards on the network.
    This function is designed to be called regularly from a FastAPI scheduler.
    """
    global recv_sock
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # The UDP port used for discovery
    GAME_STATE_PORT = 37021

    # Create socket only if it doesn't exist
    if recv_sock is None:
        try:
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            recv_sock.bind(("0.0.0.0", GAME_STATE_PORT))
            recv_sock.setblocking(False)
            logger.info(f"Created socket listening on UDP port {GAME_STATE_PORT}")
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
                logger.info(f"Received message: {msg}")
            except json.JSONDecodeError:
                continue
    except Exception as e:
        logger.error(f"Error while listening for boards: {e}")

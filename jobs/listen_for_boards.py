import json
import logging
import socket
import time
from datetime import datetime

from db.con import Machine

async def listen_for_boards() -> None:
    """
    Listen for UDP broadcasts from boards on the network.
    This function is designed to be called regularly from a FastAPI scheduler.
    """
    global known_devices, recv_sock

    

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Listening for board announcements...")

    # The UDP port used for discovery
    DISCOVERY_PORT = 37020
    DEVICE_TIMEOUT = 60  # Consider devices older than this as offline

    # Initialize the socket if not already done
    if recv_sock is None:
        try:
            recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            recv_sock.bind(("0.0.0.0", DISCOVERY_PORT))
            recv_sock.setblocking(False)
            print(f"Listening for board announcements on UDP port {DISCOVERY_PORT}")
        except Exception as e:
            print(f"Failed to set up socket: {e}")
            return

    # Process any incoming announcements
    try:
        while True:
            try:
                data, addr = recv_sock.recvfrom(1024)
            except BlockingIOError:
                # No more data available
                break

            try:
                msg = json.loads(data.decode("utf-8"))
                logging.debug(f"Received message: {msg}")
            except json.JSONDecodeError:
                # If it's not valid JSON, ignore it
                continue

            if "name" in msg and "version" in msg:
                ip_str = addr[0]
                reported_ip = msg.get("ip", ip_str)
                version = msg["version"]
                name = msg["name"]
                current_time = time.time()

                # Update our known devices dictionary
                known_devices[ip_str] = {
                    "version": version,
                    "last_seen": current_time,
                    "name": name,
                    "reported_ip": reported_ip
                }

                # Print the discovery
                print(f"Board announcement from {name} at {ip_str} (version: {version}) reported_ip: {reported_ip}")

    except Exception as e:
        print(f"Error while listening for boards: {e}")

    # Prune devices that haven't been seen in a while
    current_time = time.time()
    to_remove = []

    for ip, info in known_devices.items():
        if current_time - info["last_seen"] > DEVICE_TIMEOUT:
            to_remove.append(ip)
            print(f"Board timeout: {info['name']} at {ip} is no longer visible")

    for ip in to_remove:
        del known_devices[ip]

    # Print current known devices
    if known_devices:
        logging.info(f"Current known devices:{len(known_devices)}")
        for ip, info in known_devices.items():
            logging.info(f"  {info['name']} at {ip} (version: {info['version']}) reported_ip: {info['reported_ip']}")

    # Update the database with the known devices
    for ip, info in known_devices.items():
        await Machine.upsert(
            ip=ip,
            name=info["name"],
            version=info["version"],
            last_seen=datetime.fromtimestamp(info["last_seen"])
        )


# Global variables to maintain state between function calls
known_devices = {}
recv_sock = None

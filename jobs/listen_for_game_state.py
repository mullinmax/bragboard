import asyncio
import json
import logging
import socket
from datetime import datetime

from db.con import AsyncDatabase, Game, GameState

# Global socket variable that persists between function calls
recv_sock = None


async def listen_for_game_state() -> None:
    """
    Listen for UDP broadcasts from boards on the network.
    This function is designed to be called regularly from a FastAPI scheduler.
    """
    await GameState.initialize()

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

    # loop every 0.25 seconds
    while True:
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
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON: {e}")
                    continue

                con = await AsyncDatabase.get_instance()

                # Find the game this is for based on the IP, and if thre's an active game
                query = """
                    SELECT
                        games.id,
                        game_states.state
                    FROM machines
                    INNER JOIN games
                        ON games.machine_id = machines.id
                    LEFT JOIN game_states
                        ON game_states.game_id = games.id
                    WHERE id = $1
                        AND games.active = true
                """
                params = (msg["game_ip"],)
                result = await con.fetchone(query, params)

                if result is None:
                    new_game = await Game.new(machine_id=addr[0], date=datetime.now(), active=True)
                    game_id = new_game["id"]
                    prev_state = None
                else:
                    game_id = result["id"]
                    prev_state = result["state"]

                # If the last status is the same as this one ignore it
                if prev_state == msg["state"]:
                    continue

                # else add the new game state
                await GameState.new(
                    game_id=game_id,
                    state=msg["state"],
                    date=datetime.now(),
                )

        except Exception as e:
            logger.error(f"Error while listening for boards: {e}")

        # Sleep for a short duration to avoid busy waiting
        await asyncio.sleep(0.25)

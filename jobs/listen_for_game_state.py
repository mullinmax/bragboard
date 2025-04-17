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
                    # TODO check for malformed msgs
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
                        game_states.state,
                        games.active
                    FROM games
                    LEFT JOIN game_states
                        ON game_states.game_id = games.id
                    WHERE games.machine_id = $1
                    ORDER by games.date DESC
                """
                params = (msg["game_ip"],)
                result = await con.fetchone(query, params)

                # If no game is found, create a new one
                if result is None:
                    logger.info(f"No game found for {msg['game_ip']}, creating a new one")
                    await Game.new(
                        machine_id=msg["game_ip"],
                        date=datetime.now(),
                        active=msg["game_status"]["GameActive"],
                    )
                    result = await con.fetchone(query, params)

                # if current game is active and game in db is not, create a new game
                if msg["game_status"]["GameActive"] and not result["active"]:
                    logger.info(f"Game is active, creating a new game for {msg['game_ip']}")
                    await Game.new(machine_id=msg["game_ip"], date=datetime.now(), active=True)
                    result = await con.fetchone(query, params)

                # if the current game is not active and game in db is, set it to inactive
                if not msg["game_status"]["GameActive"] and result["active"]:
                    logger.info(f"Ending game for {msg['game_ip']}")
                    await Game.set_active(game_id=result["id"], active=False)
                    continue

                if not result["active"] and not msg["game_status"]["GameActive"]:
                    continue

                # if the game status is the same as the last one, ignore it
                if result["state"] == msg["game_status"]:
                    continue

                # else add the new game state
                await GameState.new(
                    game_id=result["id"],
                    state=json.dumps(msg["game_status"]),
                    timestamp=datetime.now(),
                )
                logger.info(f"Game state updated for {msg['game_ip']}: {msg['game_status']}")

        except Exception as e:
            logger.error(f"Error while listening for boards: {e}")
            # log a stack trace
            import traceback

            logger.error(traceback.format_exc())

        # Sleep for a short duration to avoid busy waiting
        await asyncio.sleep(0.25)

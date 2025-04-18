import asyncio
import json
import logging
import socket

from db.conn import AsyncDatabase, Play

# Global socket variable that persists between function calls
recv_sock = None


async def listen_for_game_final_score() -> None:
    await Play.initialize()

    global recv_sock
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    GAME_STATE_PORT = 37022

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

    # loop every second
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
                    logger.info(f"Received message: {msg}")
                    # example:
                    # [0, ("ABC", 42340), ("DEF", 1230), ("", 0), ("", 0)],
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON: {e}")
                    continue

                con = await AsyncDatabase.get_instance()

                # Find the most recent inactive game this is for based on the IP
                query = """
                    SELECT
                        games.id,
                        game_states.state,
                        games.active
                    FROM games
                    LEFT JOIN game_states
                        ON game_states.game_id = games.id
                    WHERE games.machine_id = $1
                        AND games.active = false
                    ORDER by games.date DESC
                """
                params = (msg["game_ip"],)
                result = await con.fetchone(query, params)

                # If no game is found, raise an error
                if result is None:
                    logger.error(f"No game found for {msg['game_ip']}")
                    continue

                # for each non zero score in the message, add a play to the game
                for player in msg["game"][1:]:  # Skip the first element which is the game number
                    # if the score is 0, skip it
                    if player[1] == 0:
                        continue

                    # Add the score
                    await Play.new(game_id=result["id"], score=player[1], initials=player[0])
                    # TODO calculate the seconds based on game states

        except Exception as e:
            logger.error(f"Error while listening for boards: {e}")
            # log a stack trace
            import traceback

            logger.error(traceback.format_exc())

        # Sleep for a short duration to avoid busy waiting
        await asyncio.sleep(1)

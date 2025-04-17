# TODO don't check boards that have not been connected for a while

import logging
from datetime import datetime

import requests

from db.con import AsyncDatabase, Game, Machine, Play


async def collect_highscores() -> None:
    """
    Collect highscores from all machines and store them in the database.
    """
    await Play.initialize()
    await Game.initialize()

    # Get all machines
    machines = await Machine.all()

    def get_highscores(machine_ip: str) -> dict:
        """
        Get highscores from a machine.

        Example:

        [
            {
                "initials": "MSM",
                "ago": "2m",
                "full_name": "Maxwell Mullin",
                "score": 2817420816,
                "rank": 1,
                "date": "02/04/2025"
            },
            {
                "initials": "PSM",
                "ago": "4m",
                "full_name": "Paul Mullin",
                "score": 312441,
                "rank": 2,
                "date": "12/05/2024"
            },
            {
                "initials": "BBB",
                "ago": "1y",
                "full_name": "Player 2",
                "score": 182398,
                "rank": 3,
                "date": "11/05/2023"
            }
        ]


        """
        try:
            response = requests.get(f"http://{machine_ip}/api/leaders")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching highscores from {machine_ip}: {e}")
            return {}

    for machine in machines:
        # Get the machine ID
        machine_ip = machine["ip"]

        # request the highscores from the machine
        highscores = get_highscores(machine_ip)

        query_template = """
            SELECT *
            FROM plays
            INNER JOIN games
                ON plays.game_id = game_id
            WHERE games.date = $1
                AND plays.score = $2
                AND plays.initials = $3
                AND games.machine_id = $4
        """

        con = await AsyncDatabase.get_instance()

        for highscore in highscores:
            highscore["date"] = datetime.strptime(highscore["date"], "%m/%d/%Y")

            # check to see if a play with the same score / date already exists
            params = (highscore["date"], highscore["score"], highscore["initials"], machine_ip)
            result = await con.fetchone(query_template, params)

            if result is not None:
                continue

            # Make a new game for the machine
            new_game = await Game.new(machine_id=machine_ip, date=highscore["date"], active=False)

            # Add the score
            await Play.new(
                game_id=new_game["id"], score=highscore["score"], initials=highscore["initials"]
            )

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from jobs.collect_highscores import collect_highscores
from jobs.listen_for_boards import listen_for_boards
from jobs.listen_for_game_final_score import listen_for_game_final_score
from jobs.listen_for_game_state import listen_for_game_state

# Scheduler instance
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    logging.info("Starting Scheduled Jobs")

    scheduler.add_job(
        func=listen_for_boards,
        trigger="interval",
        seconds=15,
        id="listen_for_boards",
        replace_existing=True,
        next_run_time=datetime.now(),
    )

    scheduler.add_job(
        func=listen_for_game_state,
        trigger="interval",
        seconds=60 * 5,
        id="listen_for_game_state",
        replace_existing=True,
        next_run_time=datetime.now(),
    )

    scheduler.add_job(
        func=collect_highscores,
        trigger="interval",
        seconds=60 * 5,
        id="collect_highscores",
        replace_existing=True,
        next_run_time=datetime.now(),
    )

    scheduler.add_job(
        func=listen_for_game_final_score,
        trigger="interval",
        seconds=60 * 5,
        id="listen_for_game_final_score",
        replace_existing=True,
        next_run_time=datetime.now(),
    )

    scheduler.start()

    yield

    logging.info("Stopping Scheduled Jobs")
    scheduler.shutdown(wait=False)

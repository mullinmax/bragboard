import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from listen_for_boards import listen_for_boards

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
    scheduler.start()

    yield

    logging.info("Stopping Scheduled Jobs")
    scheduler.shutdown(wait=False)

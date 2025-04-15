import logging
import sqlite3

import databases
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from jobs.scheduler import app_lifespan

# Define database URL
DATABASE_URL = "sqlite:///./bragboard.db"
database = databases.Database(DATABASE_URL)


# Create tables if they don't exist
def init_db():
    # Extract the file path from the URL
    db_path = DATABASE_URL.replace("sqlite:///", "")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create your tables here
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    """
    )

    conn.commit()
    conn.close()


# Register database lifecycle events
def register_db_events(app):
    @app.on_event("startup")
    async def startup():
        init_db()
        await database.connect()

    @app.on_event("shutdown")
    async def shutdown():
        await database.disconnect()


app = FastAPI(lifespan=app_lifespan)

# Mount the static files directory
app.mount("/html", StaticFiles(directory="web/html", html=True), name="static")
app.mount("/css", StaticFiles(directory="web/css", html=True), name="static")
app.mount("/js", StaticFiles(directory="web/js", html=True), name="static")
app.mount("/img", StaticFiles(directory="web/img", html=True), name="static")


@app.get("/")
async def redirect_to_index():
    return RedirectResponse(url="/html/index.html")


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "Resource not found"},
    )


@app.get("/api/random_data")
async def get_random_data():
    # Simulate some random data
    data = {"name": "John Doe", "age": 30, "city": "New York"}
    return data


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


# routes
# active games
# high scores (by all time, by week, by month, by day, by hour)
# game list
# game details
# game image

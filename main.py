import logging

import uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from db.con import AsyncDatabase, Machine
from jobs.scheduler import app_lifespan

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


@app.get("/api/machines/list")
async def machines_list():
    """
    Get the list of machines.
    """
    machines = await Machine.all()
    return JSONResponse(content=jsonable_encoder(machines))


@app.get("/api/machines/{machine_id}/highscores")
async def machine_highscores(machine_id: str):
    """
    Get the highscores for a specific machine.
    """
    query = """
        SELECT
            plays.initials,
            plays.score,
            games.date
        FROM machines
        JOIN games
            ON games.machine_id = machines.id
        JOIN plays
            ON plays.game_id = games.id
        WHERE machines.id = $1
        ORDER BY plays.score DESC
    """

    con = await AsyncDatabase.get_instance()
    result = await con.fetchall(query, (machine_id))

    return JSONResponse(content=jsonable_encoder(result))


@app.delete("/api/db/delete")
async def delete_all():
    """
    Erase all tables from the db
    """
    con = await AsyncDatabase.get_instance()
    # dropdb bragboard
    await con.execute(
        """
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                ) LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """
    )

    # mark all tables as uninitialized
    AsyncDatabase._initialized_tables = set()


@app.post("/api/db/query")
async def execute_query(query: str):
    """
    Execute a raw SQL query.
    """
    con = await AsyncDatabase.get_instance()
    result = await con.fetchall(query)
    return JSONResponse(content=jsonable_encoder(result))


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

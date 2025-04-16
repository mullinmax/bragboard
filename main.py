import logging
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
import json

from db.con import Machine, AsyncDatabase
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

    # serialize the datetime in last_seen
    for machine in machines:
        machine["last_seen"] = machine["last_seen"].isoformat() if machine["last_seen"] else None

    return JSONResponse(content={"machines": machines})

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

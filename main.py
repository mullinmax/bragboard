import logging
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from db.con import Machine
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

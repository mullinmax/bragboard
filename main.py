from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

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

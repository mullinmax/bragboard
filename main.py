import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

static_files = os.listdir("static")
for file in static_files:

    @app.get(f"/{file}")
    async def serve_file(file_name: str = file):
        return StaticFiles(directory="static")(file_name)


@app.get("/api/random_data")
async def get_random_data():
    # Simulate some random data
    data = {"name": "John Doe", "age": 30, "city": "New York"}
    return data

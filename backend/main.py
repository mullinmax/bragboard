from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve static files
app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")


@app.get("/api/hello")
async def read_root():
    return {"message": "Hello from FastAPI!"}

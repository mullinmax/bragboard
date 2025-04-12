from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Serve static files
app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")

@app.get("/api/hello")
async def read_root():
    return {"message": "Hello from FastAPI!"}
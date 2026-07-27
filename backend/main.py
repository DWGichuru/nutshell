from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.db import init_db
from backend.routes.videos import router as videos_router

FRONTEND_DIR = "frontend"

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Nutshell", lifespan=lifespan)
app.include_router(videos_router)
app.mount(f"/{FRONTEND_DIR}", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
def read_root() -> FileResponse:
    return FileResponse(f"{FRONTEND_DIR}/index.html")

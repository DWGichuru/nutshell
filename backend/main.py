import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.db import init_db
from backend.routes.videos import router as videos_router

FRONTEND_DIST_DIR = os.environ.get("NUTSHELL_FRONTEND_DIR", "frontend/dist")

load_dotenv(dotenv_path=os.environ.get("NUTSHELL_ENV_FILE"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Nutshell", lifespan=lifespan)
app.include_router(videos_router)
app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIST_DIR, html=True, check_dir=False),
    name="frontend",
)

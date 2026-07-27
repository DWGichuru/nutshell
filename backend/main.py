from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.db import init_db
from backend.routes.videos import router as videos_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="Nutshell", lifespan=lifespan)
app.include_router(videos_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "hello world"}

from fastapi import FastAPI

from backend.routes.videos import router as videos_router

app = FastAPI(title="Nutshell")
app.include_router(videos_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "hello world"}

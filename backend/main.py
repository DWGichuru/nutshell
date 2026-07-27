from fastapi import FastAPI

app = FastAPI(title="Nutshell")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "hello world"}

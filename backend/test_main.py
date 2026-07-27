from fastapi.testclient import TestClient

from backend import db
from backend.main import app


def test_read_root_serves_frontend_index():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Nutshell" in response.text


def test_startup_creates_index_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "index.db")

    with TestClient(app):
        pass

    assert (tmp_path / "index.db").exists()

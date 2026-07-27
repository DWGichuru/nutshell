from fastapi.testclient import TestClient

from backend import db
from backend.main import app, read_root


def test_read_root():
    assert read_root() == {"message": "hello world"}


def test_startup_creates_index_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "index.db")

    with TestClient(app):
        pass

    assert (tmp_path / "index.db").exists()

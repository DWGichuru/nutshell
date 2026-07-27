from backend.main import read_root


def test_read_root():
    assert read_root() == {"message": "hello world"}

from pathlib import Path
from typing import Any

from backend.models import VideoMeta

DATA_ROOT = Path("data/videos")


def derive_video_id(info: dict[str, Any]) -> str:
    return str(info["id"]).lower()


def video_dir(video_id: str) -> Path:
    path = DATA_ROOT / video_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def audio_path(video_id: str) -> Path:
    return DATA_ROOT / video_id / "audio.mp3"


def write_meta(video_id: str, meta: VideoMeta) -> None:
    meta_path = video_dir(video_id) / "meta.json"
    meta_path.write_text(meta.model_dump_json(indent=2))


def read_meta(video_id: str) -> VideoMeta:
    meta_path = DATA_ROOT / video_id / "meta.json"
    return VideoMeta.model_validate_json(meta_path.read_text())

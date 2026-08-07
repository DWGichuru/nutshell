import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.models import Transcript, VideoMeta

SUMMARY_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S%fZ"


def _resolve_data_root() -> Path:
    data_dir = os.environ.get("NUTSHELL_DATA_DIR")
    return Path(data_dir) / "videos" if data_dir else Path("data/videos")


DATA_ROOT = _resolve_data_root()


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


def transcript_path(video_id: str) -> Path:
    return DATA_ROOT / video_id / "transcript.json"


def write_transcript(video_id: str, transcript: Transcript) -> None:
    path = transcript_path(video_id)
    path.write_text(transcript.model_dump_json(indent=2))


def read_transcript(video_id: str) -> Transcript:
    return Transcript.model_validate_json(transcript_path(video_id).read_text())


@dataclass
class SummaryEntry:
    created_at: str
    content: str


def summaries_dir(video_id: str) -> Path:
    path = DATA_ROOT / video_id / "summaries"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_summary(video_id: str, content: str) -> Path:
    timestamp = datetime.now(UTC).strftime(SUMMARY_TIMESTAMP_FORMAT)
    path = summaries_dir(video_id) / f"{timestamp}.md"
    path.write_text(content)
    return path


def list_summaries(video_id: str) -> list[SummaryEntry]:
    dir_path = DATA_ROOT / video_id / "summaries"
    entries = [
        SummaryEntry(created_at=path.stem, content=path.read_text()) for path in dir_path.glob("*.md")
    ]
    entries.sort(key=lambda entry: entry.created_at, reverse=True)
    return entries

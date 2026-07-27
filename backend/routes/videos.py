from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from backend.db import upsert_video
from backend.models import (
    DownloadStartedResponse,
    DownloadStatusResponse,
    MetadataRequest,
    TrimRequest,
    TrimResponse,
    VideoMeta,
    VideoMetadataResponse,
)
from backend.storage import audio_path, derive_video_id, read_meta, video_dir, write_meta
from backend.youtube import YouTubeError, convert_to_mp3, download_audio, fetch_metadata, trim_audio

router = APIRouter(prefix="/api/videos", tags=["videos"])

DURATION_WARNING_THRESHOLD_SECONDS = 3600
TRANSCRIPTION_ESTIMATE_MULTIPLIER = 0.5

_download_status: dict[str, dict[str, str | None]] = {}


def estimate_transcription(duration_seconds: int) -> tuple[bool, float | None]:
    if duration_seconds <= DURATION_WARNING_THRESHOLD_SECONDS:
        return False, None
    estimated_minutes = round(duration_seconds * TRANSCRIPTION_ESTIMATE_MULTIPLIER / 60, 1)
    return True, estimated_minutes


@router.post("/metadata", response_model=VideoMetadataResponse)
def get_metadata(request: MetadataRequest) -> VideoMetadataResponse:
    try:
        info = fetch_metadata(request.url)
    except YouTubeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    duration_seconds = int(info.get("duration") or 0)
    needs_confirmation, estimated_minutes = estimate_transcription(duration_seconds)

    return VideoMetadataResponse(
        title=info.get("title", ""),
        channel=info.get("channel") or info.get("uploader") or "",
        duration_seconds=duration_seconds,
        needs_confirmation=needs_confirmation,
        estimated_minutes=estimated_minutes,
    )


def _run_download(video_id: str, url: str, info: dict[str, Any]) -> None:
    _download_status[video_id] = {"status": "downloading", "error": None}
    try:
        dest_dir = video_dir(video_id)
        downloaded_path = download_audio(url, dest_dir)
        convert_to_mp3(downloaded_path)
        meta = VideoMeta(
            video_id=video_id,
            title=info.get("title", ""),
            channel=info.get("channel") or info.get("uploader") or "",
            duration_seconds=int(info.get("duration") or 0),
            date_added=datetime.now(UTC).isoformat(),
            source_url=url,
        )
        write_meta(video_id, meta)
        upsert_video(meta, dest_dir)
        _download_status[video_id] = {"status": "done", "error": None}
    except Exception as exc:
        _download_status[video_id] = {"status": "error", "error": str(exc)}


@router.post("/download", response_model=DownloadStartedResponse)
def start_download(request: MetadataRequest, background_tasks: BackgroundTasks) -> DownloadStartedResponse:
    try:
        info = fetch_metadata(request.url)
    except YouTubeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    video_id = derive_video_id(info)
    _download_status[video_id] = {"status": "pending", "error": None}
    background_tasks.add_task(_run_download, video_id, request.url, info)

    return DownloadStartedResponse(video_id=video_id, status="pending")


@router.get("/{video_id}/status", response_model=DownloadStatusResponse)
def get_download_status(video_id: str) -> DownloadStatusResponse:
    status = _download_status.get(video_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Unknown video_id")
    return DownloadStatusResponse(**status)


@router.get("/{video_id}/audio")
def get_audio(video_id: str) -> FileResponse:
    path = audio_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found for video_id")
    return FileResponse(path, media_type="audio/mpeg")


@router.post("/{video_id}/trim", response_model=TrimResponse)
def trim_video_audio(video_id: str, request: TrimRequest) -> TrimResponse:
    try:
        meta = read_meta(video_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Unknown video_id") from exc

    if request.start_seconds < 0 or request.start_seconds >= request.end_seconds:
        raise HTTPException(status_code=400, detail="start_seconds must be >= 0 and less than end_seconds")
    if request.end_seconds > meta.duration_seconds:
        raise HTTPException(status_code=400, detail="end_seconds exceeds video duration")

    path = audio_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found for video_id")

    try:
        trim_audio(path, request.start_seconds, request.end_seconds)
    except YouTubeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return TrimResponse(status="trimmed", duration_seconds=request.end_seconds - request.start_seconds)

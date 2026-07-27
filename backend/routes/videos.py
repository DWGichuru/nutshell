from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.models import (
    DownloadStartedResponse,
    DownloadStatusResponse,
    MetadataRequest,
    VideoMeta,
    VideoMetadataResponse,
)
from backend.storage import derive_video_id, video_dir, write_meta
from backend.youtube import YouTubeError, convert_to_mp3, download_audio, fetch_metadata

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

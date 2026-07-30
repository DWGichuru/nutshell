from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from backend.adapters.summarization.anthropic_api import summarize as summarize_anthropic
from backend.adapters.summarization.base import SummaryInput
from backend.adapters.summarization.openai_api import summarize as summarize_openai
from backend.adapters.transcription.base import TranscriptSegment
from backend.adapters.transcription.local_mlx import transcribe as transcribe_local
from backend.adapters.transcription.openai_api import transcribe as transcribe_api
from backend.db import list_videos, upsert_video
from backend.models import (
    DownloadStartedResponse,
    DownloadStatusResponse,
    MetadataRequest,
    SummarizationStartedResponse,
    SummarizationStatusResponse,
    SummarizeRequest,
    SummaryEntryModel,
    SummaryListResponse,
    TranscribeRequest,
    Transcript,
    TranscriptionStartedResponse,
    TranscriptionStatusResponse,
    TranscriptSegmentModel,
    TrimRequest,
    TrimResponse,
    VideoListResponse,
    VideoMeta,
    VideoMetadataResponse,
    VideoSummaryModel,
)
from backend.storage import (
    audio_path,
    derive_video_id,
    list_summaries,
    read_meta,
    read_transcript,
    video_dir,
    write_meta,
    write_summary,
    write_transcript,
)
from backend.youtube import YouTubeError, convert_to_mp3, download_audio, fetch_metadata, trim_audio

router = APIRouter(prefix="/api/videos", tags=["videos"])

DURATION_WARNING_THRESHOLD_SECONDS = 3600
TRANSCRIPTION_ESTIMATE_MULTIPLIER = 0.5
MIN_TRIM_DURATION_SECONDS = 1.0

_download_status: dict[str, dict[str, str | None]] = {}
_transcription_status: dict[str, dict[str, str | None]] = {}
_summarization_status: dict[str, dict[str, str | None]] = {}


def estimate_transcription(duration_seconds: int) -> tuple[bool, float | None]:
    if duration_seconds <= DURATION_WARNING_THRESHOLD_SECONDS:
        return False, None
    estimated_minutes = round(duration_seconds * TRANSCRIPTION_ESTIMATE_MULTIPLIER / 60, 1)
    return True, estimated_minutes


@router.get("", response_model=VideoListResponse)
def get_videos(
    search: str | None = None, date_from: str | None = None, date_to: str | None = None
) -> VideoListResponse:
    rows = list_videos(search=search, date_from=date_from, date_to=date_to)
    return VideoListResponse(
        videos=[
            VideoSummaryModel(
                video_id=row[0], title=row[1], channel=row[2], duration_seconds=row[3], date_added=row[4]
            )
            for row in rows
        ]
    )


@router.get("/{video_id}", response_model=VideoMeta)
def get_video(video_id: str) -> VideoMeta:
    try:
        return read_meta(video_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Unknown video_id") from exc


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
    if request.end_seconds - request.start_seconds < MIN_TRIM_DURATION_SECONDS:
        raise HTTPException(status_code=400, detail="Trim range must be at least 1 second.")

    path = audio_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found for video_id")

    try:
        trim_audio(path, request.start_seconds, request.end_seconds)
    except YouTubeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return TrimResponse(status="trimmed", duration_seconds=request.end_seconds - request.start_seconds)


def _run_transcription(video_id: str, method: str) -> None:
    _transcription_status[video_id] = {"status": "transcribing", "error": None}
    try:
        adapter = transcribe_api if method == "api" else transcribe_local
        result = adapter(audio_path(video_id))
        transcript = Transcript(
            text=result.text,
            segments=[
                TranscriptSegmentModel(start=segment.start, end=segment.end, text=segment.text)
                for segment in result.segments
            ],
            method=result.method,
        )
        write_transcript(video_id, transcript)
        _transcription_status[video_id] = {"status": "done", "error": None}
    except Exception as exc:
        _transcription_status[video_id] = {"status": "error", "error": str(exc)}


@router.post("/{video_id}/transcribe", response_model=TranscriptionStartedResponse)
def start_transcription(
    video_id: str, request: TranscribeRequest, background_tasks: BackgroundTasks
) -> TranscriptionStartedResponse:
    try:
        read_meta(video_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Unknown video_id") from exc

    if not audio_path(video_id).exists():
        raise HTTPException(status_code=404, detail="Audio not found for video_id")

    _transcription_status[video_id] = {"status": "pending", "error": None}
    background_tasks.add_task(_run_transcription, video_id, request.method)

    return TranscriptionStartedResponse(video_id=video_id, status="pending")


@router.get("/{video_id}/transcription/status", response_model=TranscriptionStatusResponse)
def get_transcription_status(video_id: str) -> TranscriptionStatusResponse:
    status = _transcription_status.get(video_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Unknown video_id")
    return TranscriptionStatusResponse(**status)


@router.get("/{video_id}/transcript", response_model=Transcript)
def get_transcript(video_id: str) -> Transcript:
    try:
        return read_transcript(video_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transcript not found for video_id") from exc


def _run_summarization(video_id: str, provider: str, transcript: Transcript) -> None:
    _summarization_status[video_id] = {"status": "summarizing", "error": None}
    try:
        summary_input = SummaryInput(
            text=transcript.text,
            segments=[
                TranscriptSegment(start=segment.start, end=segment.end, text=segment.text)
                for segment in transcript.segments
            ],
        )
        adapter = summarize_openai if provider == "openai" else summarize_anthropic
        content = adapter(summary_input)
        write_summary(video_id, content)
        _summarization_status[video_id] = {"status": "done", "error": None}
    except Exception as exc:
        _summarization_status[video_id] = {"status": "error", "error": str(exc)}


@router.post("/{video_id}/summarize", response_model=SummarizationStartedResponse)
def start_summarization(
    video_id: str, request: SummarizeRequest, background_tasks: BackgroundTasks
) -> SummarizationStartedResponse:
    try:
        transcript = read_transcript(video_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transcript not found for video_id") from exc

    _summarization_status[video_id] = {"status": "pending", "error": None}
    background_tasks.add_task(_run_summarization, video_id, request.provider, transcript)

    return SummarizationStartedResponse(video_id=video_id, status="pending")


@router.get("/{video_id}/summarization/status", response_model=SummarizationStatusResponse)
def get_summarization_status(video_id: str) -> SummarizationStatusResponse:
    status = _summarization_status.get(video_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Unknown video_id")
    return SummarizationStatusResponse(**status)


@router.get("/{video_id}/summaries", response_model=SummaryListResponse)
def get_summaries(video_id: str) -> SummaryListResponse:
    try:
        read_meta(video_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Unknown video_id") from exc

    entries = list_summaries(video_id)
    return SummaryListResponse(
        summaries=[
            SummaryEntryModel(created_at=entry.created_at, content=entry.content) for entry in entries
        ]
    )

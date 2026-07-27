from typing import Literal

from pydantic import BaseModel


class MetadataRequest(BaseModel):
    url: str


class VideoMetadataResponse(BaseModel):
    title: str
    channel: str
    duration_seconds: int
    needs_confirmation: bool
    estimated_minutes: float | None


class VideoMeta(BaseModel):
    video_id: str
    title: str
    channel: str
    duration_seconds: int
    date_added: str
    source_url: str


class DownloadStartedResponse(BaseModel):
    video_id: str
    status: str


class DownloadStatusResponse(BaseModel):
    status: str
    error: str | None = None


class TrimRequest(BaseModel):
    start_seconds: float
    end_seconds: float


class TrimResponse(BaseModel):
    status: str
    duration_seconds: float


class TranscriptSegmentModel(BaseModel):
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    text: str
    segments: list[TranscriptSegmentModel]
    method: Literal["local", "api"]


class TranscribeRequest(BaseModel):
    method: Literal["local", "api"]


class TranscriptionStartedResponse(BaseModel):
    video_id: str
    status: str


class TranscriptionStatusResponse(BaseModel):
    status: str
    error: str | None = None


class SummarizeRequest(BaseModel):
    format: Literal["paragraph", "bullets", "chaptered"]
    provider: Literal["anthropic", "openai"] = "anthropic"


class SummarizationStartedResponse(BaseModel):
    video_id: str
    status: str


class SummarizationStatusResponse(BaseModel):
    status: str
    error: str | None = None


class SummaryEntryModel(BaseModel):
    format: str
    created_at: str
    content: str


class SummaryListResponse(BaseModel):
    summaries: list[SummaryEntryModel]


class VideoSummaryModel(BaseModel):
    video_id: str
    title: str
    channel: str
    duration_seconds: int
    date_added: str


class VideoListResponse(BaseModel):
    videos: list[VideoSummaryModel]

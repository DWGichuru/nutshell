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

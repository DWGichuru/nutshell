from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

TranscriptionMethod = Literal["local", "api"]


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    text: str
    segments: list[TranscriptSegment]
    method: TranscriptionMethod


class TranscriptionAdapter(Protocol):
    def transcribe(self, audio_path: Path) -> TranscriptResult: ...


class TranscriptionError(Exception):
    """Raised when a transcription adapter can't produce a transcript."""

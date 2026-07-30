import os
from pathlib import Path

from openai import AuthenticationError, OpenAI

from backend.adapters.transcription.base import TranscriptionError, TranscriptResult, TranscriptSegment


def transcribe(audio_path: Path) -> TranscriptResult:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise TranscriptionError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    try:
        with audio_path.open("rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
            )
    except AuthenticationError as exc:
        raise TranscriptionError("Invalid OpenAI API key. Check your .env file.") from exc
    except Exception as exc:
        raise TranscriptionError(f"OpenAI transcription failed: {exc}") from exc

    segments = [
        TranscriptSegment(start=segment.start, end=segment.end, text=segment.text)
        for segment in response.segments or []
    ]
    return TranscriptResult(text=response.text, segments=segments, method="api")

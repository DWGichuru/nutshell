from pathlib import Path

import mlx_whisper

from backend.adapters.transcription.base import TranscriptionError, TranscriptResult, TranscriptSegment

MODEL = "mlx-community/whisper-base-mlx"


def transcribe(audio_path: Path) -> TranscriptResult:
    try:
        result = mlx_whisper.transcribe(str(audio_path), path_or_hf_repo=MODEL)
    except Exception as exc:
        raise TranscriptionError(f"Local transcription failed: {exc}") from exc

    segments = [
        TranscriptSegment(start=segment["start"], end=segment["end"], text=segment["text"])
        for segment in result.get("segments", [])
    ]
    return TranscriptResult(text=result["text"], segments=segments, method="local")

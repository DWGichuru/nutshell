from dataclasses import dataclass
from typing import Literal, Protocol

from backend.adapters.transcription.base import TranscriptSegment

SummaryFormat = Literal["paragraph", "bullets", "chaptered"]
SummaryProvider = Literal["anthropic", "openai"]

FORMAT_INSTRUCTIONS = {
    "paragraph": "Write a flowing prose summary of the transcript in 2-4 paragraphs.",
    "bullets": "Write a bulleted list of the key points in the transcript.",
    "chaptered": (
        "Write a chaptered summary: break the transcript into logical sections using the "
        "provided timestamps, with a heading like `## [MM:SS] Section title` for each section "
        "followed by a short summary of that section."
    ),
}


@dataclass
class SummaryInput:
    text: str
    segments: list[TranscriptSegment]


class SummarizationAdapter(Protocol):
    def summarize(self, input: SummaryInput, format: SummaryFormat) -> str: ...


class SummarizationError(Exception):
    """Raised when a summarization adapter can't produce a summary."""


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def build_prompt(input: SummaryInput, format: SummaryFormat) -> str:
    instruction = FORMAT_INSTRUCTIONS[format]
    if format == "chaptered" and input.segments:
        transcript_block = "\n".join(
            f"[{format_timestamp(segment.start)}] {segment.text}" for segment in input.segments
        )
    else:
        transcript_block = input.text
    return f"{instruction}\n\nRespond in Markdown.\n\nTranscript:\n{transcript_block}"

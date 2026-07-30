from dataclasses import dataclass
from typing import Literal, Protocol

from backend.adapters.transcription.base import TranscriptSegment

SummaryProvider = Literal["anthropic", "openai"]

SUMMARY_INSTRUCTION = (
    "Summarize the attached video transcript. Structure the summary as follows:\n\n"
    "1. **Context** - Identify what kind of video this is (e.g. tutorial, interview, lecture, "
    "review, vlog, discussion), who's involved (roles, not necessarily names), and any stated "
    "purpose or topic established at the outset.\n\n"
    "2. **Opening** - Summarize how the video begins (framing, goals, hook, or introductory "
    "context).\n\n"
    "3. **Main content, broken into labeled sections** - Identify the distinct points, topics, "
    "or segments covered, in the order they occur. For each one:\n"
    "   - Give it a short descriptive heading prefixed with its start timestamp in "
    "`[MM:SS]` form, e.g. \"[MM:SS] Section title\" (choose whatever Markdown heading level "
    "fits under the numbered list above)\n"
    "   - Summarize the core idea, argument, or step\n"
    "   - Include specific examples, data, demonstrations, or evidence used to support it\n"
    "   - Note any notable disagreement, tangent, or contribution from other speakers, if "
    "applicable\n\n"
    "4. **Closing** - Summarize how the video concludes (takeaways, call to action, next steps, "
    "or resolution).\n\n"
    "Keep the tone neutral and descriptive rather than persuasive. Preserve the original "
    "sequence of ideas rather than reordering by importance. Condense repetitive or filler "
    "language (verbal tics, repeated phrases, digressions) rather than including it verbatim. "
    "Aim for a summary detailed enough that someone who didn't watch the video could understand "
    "its full arc and substance, but condensed enough to read in a few minutes."
)


@dataclass
class SummaryInput:
    text: str
    segments: list[TranscriptSegment]


class SummarizationAdapter(Protocol):
    def summarize(self, input: SummaryInput) -> str: ...


class SummarizationError(Exception):
    """Raised when a summarization adapter can't produce a summary."""


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def build_prompt(input: SummaryInput) -> str:
    if input.segments:
        transcript_block = "\n".join(
            f"[{format_timestamp(segment.start)}] {segment.text}" for segment in input.segments
        )
    else:
        transcript_block = input.text
    return f"{SUMMARY_INSTRUCTION}\n\nRespond in Markdown.\n\nTranscript:\n{transcript_block}"

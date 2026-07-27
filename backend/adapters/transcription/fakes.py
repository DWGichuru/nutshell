from dataclasses import dataclass


@dataclass
class FakeSegment:
    start: float
    end: float
    text: str


@dataclass
class FakeTranscription:
    text: str
    segments: list[FakeSegment]


class FakeTranscriptions:
    def __init__(self, response):
        self._response = response

    def create(self, **kwargs):
        return self._response


class FakeAudio:
    def __init__(self, response):
        self.transcriptions = FakeTranscriptions(response)


class FakeOpenAI:
    def __init__(self, response):
        self.audio = FakeAudio(response)

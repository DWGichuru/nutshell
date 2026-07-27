from dataclasses import dataclass


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeMessage:
    content: list[FakeTextBlock]


class FakeMessages:
    def __init__(self, response):
        self._response = response

    def create(self, **kwargs):
        return self._response


class FakeAnthropic:
    def __init__(self, response):
        self.messages = FakeMessages(response)


@dataclass
class FakeChatMessage:
    content: str


@dataclass
class FakeChatChoice:
    message: FakeChatMessage


@dataclass
class FakeChatCompletion:
    choices: list[FakeChatChoice]


class FakeCompletions:
    def __init__(self, response):
        self._response = response

    def create(self, **kwargs):
        return self._response


class FakeChat:
    def __init__(self, response):
        self.completions = FakeCompletions(response)


class FakeOpenAIClient:
    def __init__(self, response):
        self.chat = FakeChat(response)

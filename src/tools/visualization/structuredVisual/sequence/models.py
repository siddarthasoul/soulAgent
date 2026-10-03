from pydantic import BaseModel


class SequenceParticipant(BaseModel):
    id: str
    label: str


class SequenceMessage(BaseModel):
    source: str
    target: str
    message: str


class SequenceRequest(BaseModel):
    title: str | None = None
    participants: list[SequenceParticipant]
    messages: list[SequenceMessage]
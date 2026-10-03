from pydantic import BaseModel


class ProcessStep(BaseModel):
    id: str
    label: str
    description: str | None = None


class ProcessRequest(BaseModel):
    title: str | None = None
    steps: list[ProcessStep]
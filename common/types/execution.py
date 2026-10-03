from pydantic import BaseModel

from common.types.llm import LLMResponse
from common.types.router import QueryRoute


class ExecutionResult(BaseModel):

    route: QueryRoute

    dispatch_path: list[str]

    response: LLMResponse | str | None = None

    agent: str | None = None

    visualization: str | None = None
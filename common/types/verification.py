from pydantic import BaseModel


class VerificationResult(BaseModel):
    verified: bool
    repair_query: str | None = None
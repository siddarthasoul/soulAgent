from enum import Enum

from pydantic import BaseModel


class QueryType(str, Enum):
    CHAT = "chat"
    MATH = "math"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    RESEARCH = "research"
    CODING = "coding"


class Complexity(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"


class TaskType(str, Enum):
    EXPLANATION = "explanation"
    CALCULATION = "calculation"
    RESEARCH = "research"
    CODING = "coding"
    VISUALIZATION = "visualization"
    VERIFICATION = "verification"


class QueryTask(BaseModel):
    type: TaskType
    query: str


class QueryRoute(BaseModel):
    query_type: QueryType
    complexity: Complexity
    needs_search: bool
    needs_rag: bool
    needs_planning: bool
    tasks: list[QueryTask]
    reason: str

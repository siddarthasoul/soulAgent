from fastapi import APIRouter

from app.controller.agent import get_agent_response
from app.schemas.agent import AgentRequest

router = APIRouter()


@router.post("/chat")
async def agent_response(request: AgentRequest):
    return await get_agent_response(request)
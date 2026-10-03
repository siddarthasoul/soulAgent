from app.service.agent import ServiceAgent
from app.utils.apiResponse import ApiResponse
from app.utils.apiError import ApiError


async def get_agent_response(request):

    if not request:
        raise ApiError(
            "Request is empty",
            400
        )

    service_agent = ServiceAgent()

    response = await service_agent.get_response(request)

    if not response:
        raise ApiError(
            "Failed to get agent response",
            500
        )

    return ApiResponse(
        status_code=200,
        message="Agent response generated successfully",
        data=response,
    ).to_dict()
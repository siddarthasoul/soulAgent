from src.services.agent_service import AgentService

from app.utils.apiError import ApiError


class ServiceAgent:

    def __init__(self):
        self.agent_service = AgentService()

    async def get_response(self, request):
        try:
            response = self.agent_service.handle_user_message(
                request.message
            )
            return response

        except Exception as e:
            raise ApiError(
                f"Error in AgentService: {str(e)}",
                500
            )
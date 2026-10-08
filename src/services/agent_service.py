from pathlib import Path
from uuid import uuid4
from common.types.execution import ExecutionResult
from common.types.router import TaskType
from src.agents.chat.agent import ChatAgent
from src.agents.chemistry.agent import ChemistryAgent
from src.agents.math.agent import MathAgent
from src.agents.physics.agent import PhysicsAgent
from src.agents.research.agent import ResearchAgent
from src.agents.verification.agent import VerificationAgent
from src.agents.visualization.agent import VisualizationAgent
from src.dispatcher.dispatcher import Dispatcher
from src.router.query_router import QueryRouter
from src.core.context import AgentContext
from src.tools.calculator.tool import MathTool
from src.tools.physics.tool import PhysicsTool
from src.tools.chemistry.tool import ChemistryTool
from src.tools.research.tool import ResearchTool
from src.tools.visualization.tool import VisualizationTool
from src.rag.factory import create_rag_service
from src.tools.rag.tool import RAGTool


class AgentService:
    MAX_VERIFICATION_RETRIES = 2

    def __init__(self) -> None:
        self.chat_agent = ChatAgent()
        self.math_agent = MathAgent()
        self.physics_agent = PhysicsAgent()
        self.chemistry_agent = ChemistryAgent()
        self.research_agent = ResearchAgent()
        self.visualization_agent = VisualizationAgent()
        self.verification_agent = VerificationAgent()
        self.rag_tool = RAGTool(
            create_rag_service()
        )

        self.query_router = QueryRouter()
        self.dispatcher = Dispatcher()

    def handle_user_message(
        self,
        user_message: str,
    ) -> ExecutionResult:

        context = AgentContext(
            request_id=str(uuid4()),
            user_message=user_message,
        )

        

        context.tools.register(
            "rag",
            self.rag_tool,
        )

        context.tools.register(
            "math",
            MathTool(),
        )

        context.tools.register(
            "physics",
            PhysicsTool(),
        )

        context.tools.register(
            "chemistry",
            ChemistryTool()
        )

        context.tools.register(
            "research",
            ResearchTool(),
        )

        context.tools.register(
            "visual",
            VisualizationTool(),
        )


        route = self.query_router.route(user_message)

        context.metadata["route"] = route
        context.metadata["needs_rag"] = route.needs_rag

        dispatch_path = self.dispatcher.dispatch(route)

        context.metadata["dispatch"] = dispatch_path

        responses: list[str] = []
        visualization = None
        agents: list[str] = []

        for task in route.tasks:

            if task.type == TaskType.EXPLANATION:

                response, agent = self._run_explanation(
                    query=task.query,
                    query_type=route.query_type,
                    context=context,
                )

                responses.append(response)
                agents.append(agent)

            elif task.type == TaskType.CALCULATION:

                response, agent = self._run_calculation(
                    query=task.query,
                    query_type=route.query_type,
                    context=context,
                )

                responses.append(response)
                agents.append(agent)

            elif task.type == TaskType.VISUALIZATION:

                visualization_result, agent = (
                    self._run_visualization(
                        query=task.query,
                        query_type=route.query_type,
                        context=context,
                    )
                )

                visualization = visualization_result
                agents.append(agent)

            elif task.type == TaskType.RESEARCH:

                research_response = self.research_agent.research(
                    query=task.query,
                    context=context,
                )

                responses.append(research_response.content)
                agents.append("ResearchAgent")

            elif task.type == TaskType.CODING:

                raise NotImplementedError(
                    "CodingAgent is not implemented yet."
                )


        response = self._combine_responses(responses)

        context.metadata["agents"] = agents

        return ExecutionResult(
            route=route,
            dispatch_path=dispatch_path,
            response=response,
            agent=", ".join(agents) if agents else None,
            visualization=(
                str(visualization)
                if visualization is not None
                else None
            ),
        )

    def _run_explanation(
        self,
        query: str,
        query_type,
        context: AgentContext,
    ) -> tuple[str, str]:

        if query_type.value == "math":
            self._prepare_rag(
                context=context,
                query=query,
                category="math",
            )
            return self.math_agent.run(query, context=context), "MathAgent"

        if query_type.value == "physics":
            self._prepare_rag(
                context=context,
                query=query,
                category="physics",
            )
            return self.physics_agent.run(query, context=context), "PhysicsAgent"

        if query_type.value == "chemistry":

            self._prepare_rag(
                context=context,
                query=query,
                category="chemistry",
            )

           
            
            return self.chemistry_agent.run(query, context=context), "ChemistryAgent"
        
        self._prepare_rag(
            context=context,
            query=query,
            category="chat",
        )

        return self.chat_agent.run(query, context=context), "ChatAgent"

    def _run_calculation(
        self,
        query: str,
        query_type,
        context: AgentContext,
    ) -> tuple[str, str]:

        for attempt in range(
            self.MAX_VERIFICATION_RETRIES + 1
        ):
            response, agent = self._run_calculation_once(
                query=query,
                query_type=query_type,
                context=context,
            )

            verification = self.verification_agent.verify(
                query=query,
                result=response,
            )

            if verification.verified:
                return response, agent

            if attempt == self.MAX_VERIFICATION_RETRIES:
                raise RuntimeError(
                    "Verification failed after "
                    f"{self.MAX_VERIFICATION_RETRIES} retries."
                )

            if not verification.repair_query:
                raise RuntimeError(
                    "Verification failed without "
                    "a repair instruction."
                )

            query = (
                f"{query}\n\n"
                "Verification feedback:\n"
                f"{verification.repair_query}\n\n"
                "Fix only the identified problem."
            )

        raise RuntimeError(
            "Unexpected verification state."
        )

    def _run_calculation_once(
        self,
        query: str,
        query_type,
        context: AgentContext,
    ) -> tuple[str, str]:

        if query_type.value == "math":

            return (
                self.math_agent.run(
                    query,
                    use_tool=True,
                    context=context,
                ),
                "MathAgent",
            )

        if query_type.value == "physics":

            return (
                self.physics_agent.run(
                    query,
                    use_tool=True,
                    context=context,
                ),
                "PhysicsAgent",
            )

        if query_type.value == "chemistry":

            return (
                self.chemistry_agent.run(
                    query,
                    use_tool=True,
                    context=context,
                ),
                "ChemistryAgent",
            )

        return self.chat_agent.run(query, context=context,), "ChatAgent"

    def _run_visualization(
        self,
        query: str,
        query_type,
        context: AgentContext,
    ) -> tuple[str, str]:

        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        visualization_id = str(uuid4())
        visualization_path = (
            output_dir / f"{visualization_id}.png"
        )

        if query_type.value == "chemistry":

            result = self.chemistry_agent.run(
                query,
                use_tool=True,
                context=context,
            )

            return result, "ChemistryAgent"

        result = self.visualization_agent.run(
            query=query,
            output_path=visualization_path,
            context=context,
        )

        return str(result), "VisualizationAgent"


    def _prepare_rag(self, context: AgentContext, query: str, category: str) -> None:
        if not context.metadata.get("needs_rag", False):
            return

        rag_tool = context.tools.get("rag")

        context.metadata["rag_context"] = rag_tool.search(
            query=query,
            agent=category,
            category=category,
        )




    @staticmethod
    def _combine_responses(
        responses: list[str],
    ) -> str | None:

        if not responses:
            return None

        return "\n\n".join(responses)
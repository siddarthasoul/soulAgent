from pathlib import Path

import logging
from uuid import uuid4
from src.memory.strategy.models import StrategyStatus
from common.types.execution import ExecutionResult
from common.types.router import TaskType
from src.agents.chat.agent import ChatAgent
from src.agents.chemistry.agent import ChemistryAgent
from src.agents.math.agent import MathAgent
from src.agents.physics.agent import PhysicsAgent
from src.agents.research.agent import ResearchAgent
from src.agents.verification.agent import VerificationAgent
from src.agents.visualization.agent import VisualizationAgent
from src.core.context import AgentContext
from src.dispatcher.dispatcher import Dispatcher
from src.memory.intelligence_controller import IntelligenceController
from src.memory.experience.models import (
    EvidenceRecord,
    EvidenceType,
    ExperienceOutcome,
)
from src.rag.factory import create_rag_service
from src.router.query_router import QueryRouter
from src.tools.calculator.tool import MathTool
from src.tools.chemistry.tool import ChemistryTool
from src.tools.physics.tool import PhysicsTool
from src.tools.rag.tool import RAGTool
from src.tools.research.tool import ResearchTool
from src.tools.visualization.tool import VisualizationTool

logger = logging.getLogger(__name__)


class AgentService:

    MAX_VERIFICATION_RETRIES = 2
    MAX_MEMORY_ITEMS = 5
    MAX_STRATEGIES = 3

    def __init__(self) -> None:
        self.chat_agent = ChatAgent()
        self.math_agent = MathAgent()
        self.physics_agent = PhysicsAgent()
        self.chemistry_agent = ChemistryAgent()
        self.research_agent = ResearchAgent()
        self.visualization_agent = VisualizationAgent()
        self.verification_agent = VerificationAgent()

        self.rag_tool = RAGTool(create_rag_service())
        self.query_router = QueryRouter()
        self.dispatcher = Dispatcher()
        self.memory = IntelligenceController()
        self._ensure_builtin_strategies()

    def handle_user_message(self, user_message: str) -> ExecutionResult:
        request_id = str(uuid4())
        memory_task_id: str | None = None
        task_started = False

        try:
            task = self.memory.create_task(
                objective=user_message,
                request_id=request_id,
                metadata={"source": "agent_service"},
            )
            memory_task_id = task.task_id
            self.memory.task_manager.start_task(memory_task_id)
            task_started = True
        except Exception:
            logger.exception("Could not initialize memory task; continuing without task tracking")
            if not task_started:
                memory_task_id = None

        try:
            result, strategy_id =self._execute_user_message(
                user_message=user_message,
                request_id=request_id,
                memory_task_id=memory_task_id,
            )
        except Exception as exc:
            if memory_task_id is not None and task_started:
                try:
                    self.memory.task_manager.fail_task(
                        memory_task_id,
                        reason=f"{type(exc).__name__}: {exc}"[:1000],
                    )
                except Exception:
                    logger.exception("Could not mark memory task as failed")
            raise

        if memory_task_id is not None and task_started:
            try:
                self.memory.task_manager.complete_task(memory_task_id)
            except Exception:
                logger.exception("Could not mark memory task as completed")
            else:
                try:
                    
                    calculation_verified = (
                        len(result.route.tasks) == 1
                        and result.route.tasks[0].type == TaskType.CALCULATION
                        and result.agent is not None
                    )


                    evidence = (
                        [
                            EvidenceRecord(
                                evidence_type=EvidenceType.LLM_ASSESSMENT,
                                description=(
                                    "Calculation passed the existing "
                                    "VerificationAgent verification flow."
                                ),
                                source="VerificationAgent",
                                supports_outcome=True,
                            )
                        ]
                        if calculation_verified
                        else None
                    )
                    logger.info("Selected strategy_id=%r", strategy_id)
                    logger.info(
                        "[MEMORY] Learning started: task_id=%s strategy_id=%r",
                        memory_task_id,
                        strategy_id,
                    )

                    learned = self.memory.learn_from_task(
                        task_id=memory_task_id,
                        diagnosis=(
                            "Calculation passed verification."
                            if calculation_verified
                            else (
                                "Response generated; correctness has not "
                                "been independently verified."
                            )
                        ),
                        action=f"Executed via {result.agent or 'SOUL agent'}.",
                        outcome=(
                            ExperienceOutcome.SUCCESS
                            if calculation_verified
                            else ExperienceOutcome.UNKNOWN
                        ),
                        problem_pattern=(
                            f"{result.route.query_type.value}:"
                            f"{'calculation' if calculation_verified else 'response'}"
                        ),
                        evidence=evidence,
                        strategy_id=strategy_id,
                        verified=calculation_verified,
                        confidence=0.85 if calculation_verified else 0.0,
                        operation_key=f"agent-service:{request_id}",
                    )

                    logger.info(
                    "[MEMORY] Learning completed: experience_id=%s",
                        learned.experience_id,
                    )
                except Exception:
                    logger.exception(
                        "Could not learn from completed memory task %s",
                        memory_task_id,
                    )

        return result

    def _execute_user_message(
        self,
        user_message: str,
        request_id: str,
        memory_task_id: str | None,
    ) -> tuple[ExecutionResult, str | None]:
        context = AgentContext(
            request_id=request_id,
            user_message=user_message,
        )

        context.tools.register("rag", self.rag_tool)
        context.tools.register("math", MathTool())
        context.tools.register("physics", PhysicsTool())
        context.tools.register("chemistry", ChemistryTool())
        context.tools.register("research", ResearchTool())
        context.tools.register("visual", VisualizationTool())

        route = self.query_router.route(user_message)
        context.metadata["route"] = route
        context.metadata["needs_rag"] = route.needs_rag

        memory_context = self._retrieve_memory(
            query=user_message,
            task_type=self._task_type_for_memory(route.query_type.value),
            task_id=memory_task_id,
        )

        logger.info(
            "[MEMORY DEBUG] experiences=%d strategies=%d",
            len(memory_context.get("experiences", [])),
            len(memory_context.get("strategies", [])),
        )

        strategies = memory_context.get("strategies", [])

        strategy_id = (
            strategies[0]["strategy_id"]
            if strategies and isinstance(strategies[0], dict)
            else None
        )

        if not strategy_id:
            logger.error(
                "[MEMORY] No strategy selected for task_type=%s",
                self._task_type_for_memory(route.query_type.value),
            )
        else:
            logger.info("[MEMORY] Selected strategy_id=%s", strategy_id)

        logger.info(
            "[MEMORY DEBUG] selected_strategy_id=%r",
            strategy_id,
        )

        context.metadata["memory"] = memory_context

        dispatch_path = self.dispatcher.dispatch(route)
        context.metadata["dispatch"] = dispatch_path

        responses: list[str] = []
        visualization = None
        agents: list[str] = []

        for task in route.tasks:
            task_query = self._add_memory_context(task.query, memory_context)

            if task.type == TaskType.EXPLANATION:
                response, agent = self._run_explanation(
                    query=task_query,
                    query_type=route.query_type,
                    context=context,
                )
                responses.append(response)
                agents.append(agent)

            elif task.type == TaskType.CALCULATION:
                response, agent = self._run_calculation(
                    query=task_query,
                    query_type=route.query_type,
                    context=context,
                )
                responses.append(response)
                agents.append(agent)

            elif task.type == TaskType.VISUALIZATION:
                visualization_result, agent = self._run_visualization(
                    query=task_query,
                    query_type=route.query_type,
                    context=context,
                )
                visualization = visualization_result
                agents.append(agent)

            elif task.type == TaskType.RESEARCH:
                research_response = self.research_agent.research(
                    query=task_query,
                    context=context,
                )
                responses.append(research_response.content)
                agents.append("ResearchAgent")

            elif task.type == TaskType.CODING:
                raise NotImplementedError("CodingAgent is not implemented yet.")

        response = self._combine_responses(responses)
        context.metadata["agents"] = agents

        result = ExecutionResult(
            route=route,
            dispatch_path=dispatch_path,
            response=response,
            agent=", ".join(agents) if agents else None,
            visualization=str(visualization) if visualization is not None else None,
        )

        return result, strategy_id

    @staticmethod
    def _task_type_for_memory(route_type: str) -> str:

        value = (route_type or "general").strip().lower()
        if value in {"math", "physics", "chemistry"}:
            return value
        if value in {"coding", "programming", "software"}:
            return "coding"
        if value in {"research", "web_research"}:
            return "research"
        return "general"

    def _retrieve_memory(
        self,
        query: str,
        task_type: str,
        task_id: str | None,
    ) -> dict[str, object]:
        experiences = []
        strategies = []

    # Retrieve previous experiences independently.
        try:
            experiences = self.memory.retrieve_experiences(
                query,
                verified_only=True,
                limit=self.MAX_MEMORY_ITEMS,
            )
        except Exception:
            logger.exception("[MEMORY] Experience retrieval failed")

        # Retrieve strategies independently.
        try:
            recommendations = self.memory.recommend_strategies(
                task_type=task_type,
                limit=self.MAX_STRATEGIES,
            )

            logger.info(
                "[MEMORY DEBUG] task_type=%r recommendations=%s",
                task_type,
                [
                    (item.strategy.name, str(item.strategy.strategy_id))
                        for item in recommendations
                ],
            )

            strategies = [
                {
                    "strategy_id": item.strategy.strategy_id,
                    "name": item.strategy.name,
                    "description": item.strategy.description,
                    "steps": item.strategy.steps,
                    "reason": item.reason,
                    "score": item.score,
                }
                for item in recommendations
            ]
        except Exception:
            logger.exception("[MEMORY] Strategy recommendation failed")

        logger.info(
            "[MEMORY] Retrieved %d experiences and %d strategies "
            "for task_type=%s",
            len(experiences),
            len(strategies),
            task_type,
        )

        return {
            "task_id": task_id,
            "experiences": [
                {
                    "problem_pattern": item.problem_pattern,
                    "diagnosis": item.diagnosis,
                    "action": item.action,
                    "outcome": item.outcome.value,
                    "confidence": item.confidence,
                }
                for item in experiences
            ],
            "strategies": strategies,
        }


    @staticmethod
    def _add_memory_context(query: str, memory: dict[str, object]) -> str:

        experiences = memory.get("experiences", [])
        strategies = memory.get("strategies", [])
        if not experiences and not strategies:
            return query

        lines = [
            "Relevant SOUL memory (use only when applicable; current request takes priority):"
        ]

        if experiences:
            lines.append("Previously verified experiences:")
            for index, item in enumerate(experiences, start=1):
                if not isinstance(item, dict):
                    continue
                lines.append(
                    f"{index}. Pattern: {item.get('problem_pattern')}; "
                    f"diagnosis: {item.get('diagnosis')}; "
                    f"action: {item.get('action')}; "
                    f"outcome: {item.get('outcome')}; "
                    f"confidence: {item.get('confidence')}."
                )

        if strategies:
            lines.append("Suggested strategies (recommendations, not mandatory rules):")
            for index, item in enumerate(strategies, start=1):
                if not isinstance(item, dict):
                    continue
                steps = item.get("steps", [])
                step_text = " -> ".join(str(step) for step in steps) if isinstance(steps, list) else str(steps)
                lines.append(
                    f"{index}. {item.get('name')}: {item.get('description')}. "
                    f"Steps: {step_text}. Reason: {item.get('reason')}."
                )

        return f"{query}\n\n" + "\n".join(lines)

    def _run_explanation(
        self,
        query: str,
        query_type,
        context: AgentContext,
    ) -> tuple[str, str]:
        if query_type.value == "math":
            self._prepare_rag(context=context, query=query, category="math")
            return self.math_agent.run(query, context=context), "MathAgent"

        if query_type.value == "physics":
            self._prepare_rag(context=context, query=query, category="physics")
            return self.physics_agent.run(query, context=context), "PhysicsAgent"

        if query_type.value == "chemistry":
            self._prepare_rag(context=context, query=query, category="chemistry")
            return self.chemistry_agent.run(query, context=context), "ChemistryAgent"

        self._prepare_rag(context=context, query=query, category="chat")
        return self.chat_agent.run(query, context=context), "ChatAgent"

    def _run_calculation(
        self,
        query: str,
        query_type,
        context: AgentContext,
    ) -> tuple[str, str]:
        for attempt in range(self.MAX_VERIFICATION_RETRIES + 1):
            response, agent = self._run_calculation_once(
                query=query,
                query_type=query_type,
                context=context,
            )
            verification = self.verification_agent.verify(query=query, result=response)

            if verification.verified:
                return response, agent

            if attempt == self.MAX_VERIFICATION_RETRIES:
                raise RuntimeError(
                    f"Verification failed after {self.MAX_VERIFICATION_RETRIES} retries."
                )

            if not verification.repair_query:
                raise RuntimeError("Verification failed without a repair instruction.")

            query = (
                f"{query}\n\nVerification feedback:\n"
                f"{verification.repair_query}\n\nFix only the identified problem."
            )

        raise RuntimeError("Unexpected verification state.")

    def _run_calculation_once(
        self,
        query: str,
        query_type,
        context: AgentContext,
    ) -> tuple[str, str]:
        if query_type.value == "math":
            return self.math_agent.run(query, use_tool=True, context=context), "MathAgent"

        if query_type.value == "physics":
            return self.physics_agent.run(query, use_tool=True, context=context), "PhysicsAgent"

        if query_type.value == "chemistry":
            return self.chemistry_agent.run(query, use_tool=True, context=context), "ChemistryAgent"

        return self.chat_agent.run(query, context=context), "ChatAgent"

    def _run_visualization(
        self,
        query: str,
        query_type,
        context: AgentContext,
    ) -> tuple[str, str]:
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        visualization_path = output_dir / f"{uuid4()}.png"

        if query_type.value == "chemistry":
            return (
                self.chemistry_agent.run(query, use_tool=True, context=context),
                "ChemistryAgent",
            )

        result = self.visualization_agent.run(
            query=query,
            output_path=visualization_path,
            context=context,
        )
        return str(result), "VisualizationAgent"

    def _prepare_rag(
        self,
        context: AgentContext,
        query: str,
        category: str,
    ) -> None:
        if not context.metadata.get("needs_rag", False):
            return

        rag_tool = context.tools.get("rag")
        context.metadata["rag_context"] = rag_tool.search(
            query=query,
            agent=category,
            category=category,
        )


    def _ensure_builtin_strategies(self) -> None:
        manager = self.memory.strategy_manager

        builtins = [
            {
                "name": "Stepwise mathematical reasoning",
                "description": "Solve mathematical problems step by step and verify the result.",
                "task_type": "math",
                "problem_pattern": "mathematical_problem",
                "steps": [
                "Identify the known values",
                "Choose the appropriate method",
                "Calculate the result",
                "Verify the result",
                ],
            },
            {
                "name": "Stepwise physics reasoning",
                "description": "Solve physics problems using equations and units.",
                "task_type": "physics",
                "problem_pattern": "physics_problem",
                "steps": [
                    "Identify known values and unknowns",
                    "Choose the governing equation",
                    "Calculate with consistent units",
                    "Check the result",
                ],
            },
            {
                "name": "Structured chemistry reasoning",
                "description": "Solve chemistry problems using relevant principles and checks.",
                "task_type": "chemistry",
                "problem_pattern": "chemistry_problem",
                "steps": [
                    "Identify the chemistry concept",
                    "Apply the relevant principle",
                    "Work through the solution",
                    "Check chemical consistency",
                ],
            },
            {
                "name": "Evidence-based research",
                "description": "Research a question using relevant sources and evidence.",
                "task_type": "research",
                "problem_pattern": "research_question",
                "steps": [
                    "Break down the question",
                    "Gather relevant sources",
                    "Compare the evidence",
                    "Summarize supported findings",
                ],
            },
            {
                "name": "Structured general reasoning",
                "description": "Break a problem into manageable steps and check the response.",
                "task_type": "general",
                "problem_pattern": "general_question",
                "steps": [
                    "Identify the objective",
                    "Break down the problem",
                    "Develop a response",
                    "Check relevance and consistency",
                ],
            },
        ]

        
        existing_strategies = {
            strategy.name: strategy
            for strategy in manager.list_strategies()
        }

        registered = 0
        activated = 0

        for builtin in builtins:
            strategy = existing_strategies.get(builtin["name"])

            if strategy is None:
                strategy = manager.register_strategy(**builtin)
                registered += 1

            # Built-in strategies must be eligible for selection.
            if strategy.status != StrategyStatus.ACTIVE:
                strategy = manager.set_strategy_status(
                    strategy.strategy_id,
                    StrategyStatus.ACTIVE,
                )
                activated += 1

        logger.info(
            "Built-in strategies initialized: registered=%d activated=%d",
            registered,
            activated,
        )



    @staticmethod
    def _combine_responses(responses: list[str]) -> str | None:
        if not responses:
            return None
        return "\n\n".join(responses)




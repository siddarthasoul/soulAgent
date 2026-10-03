from common.prompts.agents.research import RESEARCH_AGENT_SYSTEM_PROMPT
from common.types.llm import LLMRequest, LLMResponse
from common.types.research import ResearchResult

from src.providers.base import LLMProvider
from src.tools.research.tool import ResearchTool
from src.providers.nvidia import NvidiaProvider


class ResearchAgent:

    def __init__(
        self,
        provider: LLMProvider | None = None,
        research_tool: ResearchTool | None = None,
    ) -> None:
        self.provider = provider or NvidiaProvider()
        self.research_tool = research_tool or ResearchTool()

    def research(
        self,
        query: str,
        count: int = 5,
        top_k: int = 2,
    ) -> LLMResponse:

        research_result: ResearchResult = (
            self.research_tool.research(
                query=query,
                count=count,
                top_k=top_k,
            )
        )

        research_context = self._build_context(
            research_result
        )

        request = LLMRequest(
            task="research_answer",
            messages=[
                {
                    "role": "system",
                    "content": RESEARCH_AGENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"Research question:\n{query}\n\n"
                        f"Research data:\n{research_context}\n\n"
                        "Using the research data above, write a clear "
                        "and accurate answer to the user's question. "
                        "Use only information supported by the research."
                    ),
                },
            ],
        )

        return self.provider.generate(request)

    @staticmethod
    def _build_context(
        result: ResearchResult,
    ) -> str:

        sections = [
            f"Query: {result.query}",
            "",
            "Research:",
            result.formatted_output,
            "",
            "Sources:",
        ]

        for source in result.top_sources:
            sections.append(
                f"- {source.result.title}"
            )
            sections.append(
                f"  URL: {source.result.url}"
            )

        return "\n".join(sections)

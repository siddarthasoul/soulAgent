from src.rag.service import RAGService


class RAGTool:
    def __init__(self, rag_service: RAGService) -> None:
        self.rag_service = rag_service

    def search(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int | None = None,
        agent: str | None = None,
        category: str | None = None,
    ) -> str:
        return self.rag_service.generate(
            query=query,
            top_k=top_k,
            candidate_k=candidate_k,
            agent=agent,
            category=category,
        )
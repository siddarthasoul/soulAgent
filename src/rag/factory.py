from sentence_transformers import SentenceTransformer

from src.rag.relevance import RelevanceGate
from src.rag.reranking.reranker import Reranker
from src.rag.retrieval.retriever import Retriever
from src.rag.service import RAGService


def create_rag_service() -> RAGService:
    embedding_model = SentenceTransformer(
        "BAAI/bge-small-en-v1.5",
        device="cuda",
    )

    reranker = Reranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        device="cuda",
    )

    retriever = Retriever(
        model=embedding_model,
        reranker=reranker,
    )


    relevance_gate = RelevanceGate(
        min_score=0.0,
    )

    return RAGService(
        retriever=retriever,
        relevance_gate=relevance_gate,
    )
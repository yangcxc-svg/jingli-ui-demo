from app.rag.retriever import RetrievedChunk


class Reranker:
    async def rerank(self, query: str, chunks: list[RetrievedChunk], top_k: int = 5) -> list[RetrievedChunk]:
        return chunks[:top_k]


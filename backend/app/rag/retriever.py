from pydantic import BaseModel

from app.rag.store import KnowledgeStore


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float


class Retriever:
    def __init__(self) -> None:
        self.store = KnowledgeStore()

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        hits = self.store.search(query, top_k=top_k)
        return [
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                score=score,
            )
            for chunk, score in hits
        ]
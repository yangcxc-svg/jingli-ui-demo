from app.rag.retriever import RetrievedChunk


class PromptBuilder:
    def build_rag_prompt(self, question: str, chunks: list[RetrievedChunk]) -> str:
        context = "\n\n".join(chunk.text for chunk in chunks)
        return f"Question:\n{question}\n\nContext:\n{context}"


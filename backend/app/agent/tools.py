from app.rag.retriever import Retriever


class AgentTools:
    def __init__(self) -> None:
        self.retriever = Retriever()

    async def search_knowledge(self, query: str) -> list[dict[str, object]]:
        chunks = await self.retriever.retrieve(query)
        return [chunk.model_dump() for chunk in chunks]

    async def search_products(self, query: str) -> list[dict[str, object]]:
        return []

    async def compare_products(self, product_ids: list[str]) -> dict[str, object]:
        return {"product_ids": product_ids, "differences": []}

    async def get_product_detail(self, product_id: str) -> dict[str, object]:
        return {"product_id": product_id}

    async def parse_image(self, image_id: str) -> dict[str, object]:
        return {"image_id": image_id, "text": ""}


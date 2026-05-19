from collections.abc import AsyncIterator

from app.agent.prompts import (
    CHAT_RECOMMENDATION_PROMPT_VERSION,
    GUIDE_SYSTEM_PROMPT,
)
from app.agent.state import AgentResult
from app.agent.tools import AgentTools
from app.llm.client import ChatMessage, ImageRef, LLMClient
from app.schemas.chat import Citation, IntentState
from app.services.image_service import ImageService


def _is_vision_model(model: str) -> bool:
    m = (model or "").lower()
    # 覆盖常见多模态模型命名
    return any(
        tag in m
        for tag in ("vl", "vision", "4v", "4o", "llava", "omni", "vlm")
    )


class GuideAgent:
    def __init__(self) -> None:
        self.tools = AgentTools()
        self.llm = LLMClient()
        self.images = ImageService()
        self.vision_enabled = _is_vision_model(self.llm.model)

    async def run(
        self,
        message: str,
        conversation_id: str,
        image_ids: list[str] | None = None,
        history: list[ChatMessage] | None = None,
        candidate_products: list[dict[str, object]] | None = None,
    ) -> AgentResult:
        intent = IntentState(intent="product_consultation")
        chunks = await self.tools.search_knowledge(message)
        prompt = self._build_prompt(
            message, chunks, image_ids or [], candidate_products or []
        )
        image_refs = self._build_image_refs(image_ids or [])
        result = await self.llm.generate(
            prompt,
            system=GUIDE_SYSTEM_PROMPT,
            images=image_refs,
            history=history,
            prompt_name="chat_recommendation",
            prompt_version=CHAT_RECOMMENDATION_PROMPT_VERSION,
        )
        citations = self._build_citations(chunks)
        return AgentResult(answer=result.text, intent=intent, citations=citations)

    async def astream(
        self,
        message: str,
        conversation_id: str,
        image_ids: list[str] | None = None,
        history: list[ChatMessage] | None = None,
        candidate_products: list[dict[str, object]] | None = None,
    ) -> AsyncIterator[str]:
        chunks = await self.tools.search_knowledge(message)
        prompt = self._build_prompt(
            message, chunks, image_ids or [], candidate_products or []
        )
        image_refs = self._build_image_refs(image_ids or [])
        async for delta in self.llm.astream(
            prompt,
            system=GUIDE_SYSTEM_PROMPT,
            images=image_refs,
            history=history,
            prompt_name="chat_recommendation",
            prompt_version=CHAT_RECOMMENDATION_PROMPT_VERSION,
        ):
            yield delta

    # ---------- helpers ----------

    def _build_image_refs(self, image_ids: list[str]) -> list[ImageRef]:
        """仅在使用 vision 模型时把图片传给 LLM，否则降级为文字提示。"""
        if not image_ids or not self.vision_enabled:
            return []
        refs: list[ImageRef] = []
        for iid in image_ids:
            stored = self.images.get(iid)
            if not stored:
                continue
            refs.append(
                ImageRef(path=stored.path, content_type=stored.content_type)
            )
        return refs

    def _build_prompt(
        self,
        message: str,
        chunks: list[dict[str, object]],
        image_ids: list[str],
        candidate_products: list[dict[str, object]] | None = None,
    ) -> str:
        from app.agent.prompts import build_chat_recommendation_prompt

        image_hint: str | None = None
        if image_ids:
            names: list[str] = []
            for iid in image_ids:
                stored = self.images.get(iid)
                names.append(stored.filename if stored else iid)
            if self.vision_enabled:
                image_hint = (
                    f"用户附加了 {len(image_ids)} 张图片（文件名：{', '.join(names)}）。"
                    "请直接基于图片内容回答；如果图片中是商品，请结合知识库片段"
                    "做参数核对、推荐与对比；如果信息不充分，再向用户追问。"
                )
            else:
                image_hint = (
                    f"用户附加了 {len(image_ids)} 张图片（文件名：{', '.join(names)}）。"
                    "当前模型不支持直接读图，请基于文件名/常识做合理推测，"
                    "并主动询问用户图片中的关键信息（如商品名称、参数、使用场景）。"
                )

        return build_chat_recommendation_prompt(
            message=message,
            chunks=chunks,
            image_hint=image_hint,
            candidate_products=candidate_products,
        )

    @staticmethod
    def _build_citations(chunks: list[dict[str, object]]) -> list[Citation]:
        citations: list[Citation] = []
        for c in chunks[:5]:
            try:
                citations.append(
                    Citation(
                        document_id=str(c.get("document_id", "")),
                        chunk_id=str(c.get("chunk_id", "")),
                        text=str(c.get("text", "")),
                    )
                )
            except Exception:  # noqa: BLE001
                continue
        return citations

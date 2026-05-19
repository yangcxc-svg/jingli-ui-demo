from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from app.agent.tools import AgentTools
from app.schemas.gift_intent import GiftIntent
from app.services.seed_product_loader import seed_product_catalog

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_WORD_RE = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True)
class RetrievedProduct:
    product: dict[str, Any]
    score: float
    source: str


@dataclass(frozen=True)
class HybridRetrievalResult:
    keyword_chunks: list[dict[str, object]]
    semantic_products: list[RetrievedProduct]
    source_counts: dict[str, int]


class RetrievalService:
    """Hybrid product retrieval for the recommendation pipeline.

    R5 先提供可替换的本地语义向量召回：把查询和商品 embedding 文本都转为
    稀疏 token 向量，用余弦相似度做 Top K。后续接真实 embedding/向量库时，
    替换 semantic_recall 即可，推荐主流程不需要感知实现细节。
    """

    _SEMANTIC_ALIASES: dict[str, tuple[str, ...]] = {
        "面子": ("体面", "有档次", "正式", "高级", "品质", "品牌", "高端", "拿得出手"),
        "体面": ("面子", "有档次", "正式", "高级", "品质", "品牌", "高端"),
        "别太贵": ("性价比", "预算", "价格", "实惠", "不贵", "划算", "中端"),
        "不贵": ("性价比", "预算", "价格", "实惠", "划算", "中端"),
        "性价比": ("别太贵", "预算", "价格", "实惠", "划算"),
        "正式": ("体面", "商务", "高端", "品质", "见家长", "领导"),
        "浪漫": ("情侣", "纪念", "仪式感", "心意", "精致"),
        "健康": ("养生", "长辈", "按摩", "实用", "关怀"),
        "实用": ("日常", "耐用", "家用", "通勤", "高频使用"),
        "颜值": ("精致", "好看", "设计", "仪式感", "女生"),
    }

    def __init__(self, tools: AgentTools | None = None) -> None:
        self.tools = tools or AgentTools()

    async def hybrid_recall(
        self,
        query: str,
        intent: GiftIntent,
        *,
        top_k: int = 20,
    ) -> HybridRetrievalResult:
        keyword_chunks = await self.keyword_recall(query, top_k=top_k)
        try:
            semantic_products = self.semantic_recall(
                self._semantic_query_text(query, intent),
                top_k=top_k,
            )
        except Exception:  # noqa: BLE001
            semantic_products = []
        return HybridRetrievalResult(
            keyword_chunks=keyword_chunks,
            semantic_products=semantic_products,
            source_counts={
                "keyword": len({str(chunk.get("document_id") or "") for chunk in keyword_chunks}),
                "semantic": len(semantic_products),
            },
        )

    async def keyword_recall(self, query: str, *, top_k: int = 20) -> list[dict[str, object]]:
        try:
            chunks = await self.tools.retriever.retrieve(query, top_k=top_k)
            return [chunk.model_dump() for chunk in chunks]
        except AttributeError:
            chunks = await self.tools.search_knowledge(query)
            return chunks[:top_k]
        except Exception:  # noqa: BLE001
            return []

    def semantic_recall(self, query: str, *, top_k: int = 20) -> list[RetrievedProduct]:
        try:
            query_vector = self._vectorize(query)
            if not query_vector:
                return []

            hits: list[RetrievedProduct] = []
            for product in seed_product_catalog.list_products():
                product_id = str(product.get("product_id") or "")
                if not product_id:
                    continue
                product_vector = self._vectorize(self._product_embedding_text(product))
                score = self._cosine(query_vector, product_vector)
                if score > 0:
                    hits.append(
                        RetrievedProduct(product=product, score=round(score, 4), source="semantic")
                    )
            hits.sort(key=lambda item: item.score, reverse=True)
            return hits[:top_k]
        except Exception:  # noqa: BLE001
            return []

    @classmethod
    def _semantic_query_text(cls, query: str, intent: GiftIntent) -> str:
        return " ".join(
            item
            for item in [
                query,
                intent.recipient,
                intent.relationship,
                intent.scenario,
                " ".join(intent.scenarios),
                " ".join(intent.target_people),
                " ".join(intent.preferences),
                " ".join(intent.gift_style),
                intent.budget_level,
            ]
            if item
        )

    @classmethod
    def _product_embedding_text(cls, product: dict[str, Any]) -> str:
        parts: list[str] = []
        for key in [
            "brand",
            "series",
            "name",
            "category",
            "subcategory",
            "budget_level",
            "knowledge_text",
        ]:
            value = product.get(key)
            if value:
                parts.append(str(value))

        for key in [
            "scenarios",
            "target_people",
            "target_users",
            "use_cases",
            "tags",
            "comparison_tags",
            "highlights",
            "pros",
            "avoid_for",
            "not_recommended_for",
        ]:
            value = product.get(key)
            if isinstance(value, list):
                parts.extend(str(item) for item in value if str(item).strip())

        rating = product.get("rating")
        if isinstance(rating, dict) and rating.get("summary"):
            parts.append(str(rating["summary"]))

        return " ".join(parts)

    @classmethod
    def _vectorize(cls, text: str) -> dict[str, float]:
        tokens = cls._expand_tokens(cls._tokenize(text))
        vector: dict[str, float] = {}
        for token in tokens:
            vector[token] = vector.get(token, 0.0) + 1.0
        return vector

    @classmethod
    def _expand_tokens(cls, tokens: list[str]) -> list[str]:
        expanded: list[str] = []
        for token in tokens:
            expanded.append(token)
            expanded.extend(cls._SEMANTIC_ALIASES.get(token, ()))
        return expanded

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        tokens = _WORD_RE.findall(text)
        cjk = "".join(_CJK_RE.findall(text))
        tokens.extend(cjk[i : i + 2] for i in range(len(cjk) - 1))

        # 保留少量常见短语，弥补 2-gram 对表达语义的切碎。
        phrase_candidates = [
            "有面子",
            "别太贵",
            "性价比",
            "仪式感",
            "见家长",
            "送领导",
            "送客户",
            "生日",
            "婚礼",
            "订婚",
            "乔迁",
            "长辈",
            "女生",
            "男生",
        ]
        tokens.extend(phrase for phrase in phrase_candidates if phrase in text)
        return tokens

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(value * right.get(token, 0.0) for token, value in left.items())
        if dot <= 0:
            return 0.0
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

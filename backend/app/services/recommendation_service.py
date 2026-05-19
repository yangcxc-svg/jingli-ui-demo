from __future__ import annotations

from decimal import Decimal

from app.schemas.gift_intent import GiftIntent
from app.schemas.product import ProductCard
from app.schemas.recommendation import RecommendationRequest, RecommendationResult
from app.schemas.recommendation_score import ProductScore
from app.services.intent_extractor import IntentExtractor
from app.services.product_scorer import ProductScorer
from app.services.retrieval_service import RetrievedProduct, RetrievalService
from app.services.seed_product_loader import seed_product_catalog


class RecommendationService:
    """Shared product recommendation utilities for chat and gift-plan flows."""

    def __init__(self) -> None:
        self.retrieval_service = RetrievalService()
        self.intent_extractor = IntentExtractor()
        self.product_scorer = ProductScorer()

    async def recommend_products(self, request: RecommendationRequest) -> RecommendationResult:
        intent = await self._resolve_intent(request)
        enriched = self._enrich_request(request, intent)
        query = self._build_query(enriched)
        retrieval = await self.retrieval_service.hybrid_recall(
            query=query,
            intent=intent,
            top_k=enriched.max_candidates,
        )
        chunks = retrieval.keyword_chunks
        structured_candidates = self.structured_recall_candidates(
            budget=enriched.budget,
            budget_level=enriched.budget_level,
            scenarios=enriched.scenarios,
            target_people=enriched.target_people,
            max_candidates=enriched.max_candidates,
        )
        knowledge_candidates = self.build_product_candidates(
            chunks=chunks,
            budget=enriched.budget,
            budget_level=enriched.budget_level,
            scenarios=enriched.scenarios,
            target_people=enriched.target_people,
            max_products=enriched.max_candidates,
        )
        semantic_candidates = self.build_semantic_candidates(
            retrieved_products=retrieval.semantic_products,
            budget=enriched.budget,
            max_products=enriched.max_candidates,
        )
        candidates = self._merge_candidates(
            [structured_candidates, knowledge_candidates, semantic_candidates]
        )

        relaxed_candidates: list[tuple[ProductCard, dict[str, object]]] = []
        if not candidates and (enriched.scenarios or enriched.target_people):
            relaxed_knowledge = self.build_product_candidates(
                chunks=chunks,
                budget=enriched.budget,
                budget_level=enriched.budget_level,
                max_products=enriched.max_candidates,
            )
            relaxed_structured = self.structured_recall_candidates(
                budget=enriched.budget,
                budget_level=enriched.budget_level,
                max_candidates=enriched.max_candidates,
            )
            relaxed_semantic = self.build_semantic_candidates(
                retrieved_products=retrieval.semantic_products,
                budget=enriched.budget,
                max_products=enriched.max_candidates,
            )
            relaxed_candidates = self._merge_candidates(
                [relaxed_knowledge, relaxed_structured, relaxed_semantic]
            )
            candidates = relaxed_candidates

        fallback_candidates: list[tuple[ProductCard, dict[str, object]]] = []
        if not candidates and enriched.include_fallback:
            fallback_candidates = self.fallback_candidates(
                budget=enriched.budget,
                budget_level=enriched.budget_level,
                scenarios=enriched.scenarios,
                target_people=enriched.target_people,
                max_products=enriched.max_candidates,
            )
            if not fallback_candidates and (enriched.scenarios or enriched.target_people):
                fallback_candidates = self.fallback_candidates(
                    budget=enriched.budget,
                    budget_level=enriched.budget_level,
                    max_products=enriched.max_candidates,
                )
            if not fallback_candidates and enriched.budget_level:
                fallback_candidates = self.fallback_candidates(
                    budget=enriched.budget,
                    max_products=enriched.max_candidates,
                )
            candidates = fallback_candidates

        ranked = self._rank_candidates(candidates, intent)[: enriched.max_products]
        products = [
            card.model_copy(update={"reason": score.reasons[0] if score.reasons else card.reason})
            for card, _, score in ranked
        ]

        return RecommendationResult(
            products=products,
            citations=[chunk for chunk in chunks if chunk.get("text")],
            intent=intent,
            scores=[score for _, _, score in ranked],
            pipeline={
                "structured_recall_count": len(structured_candidates),
                "knowledge_recall_count": len(knowledge_candidates),
                "semantic_recall_count": len(semantic_candidates),
                "relaxed_recall_count": len(relaxed_candidates),
                "fallback_recall_count": len(fallback_candidates),
                "candidate_count": len(candidates),
                "returned_count": len(ranked),
            },
        )

    def structured_recall_candidates(
        self,
        budget: Decimal | None = None,
        budget_level: str | None = None,
        scenarios: list[str] | None = None,
        target_people: list[str] | None = None,
        max_candidates: int = 20,
    ) -> list[tuple[ProductCard, dict[str, object]]]:
        candidates: list[tuple[ProductCard, dict[str, object]]] = []
        running_total = Decimal("0")
        for product in seed_product_catalog.list_products():
            product_id = str(product.get("product_id") or "")
            if not product_id:
                continue
            if not self._matches_filters(
                product=product,
                budget_level=budget_level,
                scenarios=scenarios,
                target_people=target_people,
            ):
                continue

            card = self.product_to_card(product_id, product)
            if self._exceeds_budget(
                current_total=running_total,
                next_price=card.price,
                budget=budget,
                has_existing_cards=bool(candidates),
            ):
                continue

            candidates.append((card, product))
            running_total += card.price or Decimal("0")
            if len(candidates) >= max_candidates:
                break
        return candidates

    def build_product_cards(
        self,
        chunks: list[dict[str, object]],
        budget: Decimal | None = None,
        budget_level: str | None = None,
        scenarios: list[str] | None = None,
        target_people: list[str] | None = None,
        max_products: int = 3,
    ) -> list[ProductCard]:
        return [
            card
            for card, _product in self.build_product_candidates(
                chunks=chunks,
                budget=budget,
                budget_level=budget_level,
                scenarios=scenarios,
                target_people=target_people,
                max_products=max_products,
            )
        ]

    def build_product_candidates(
        self,
        chunks: list[dict[str, object]],
        budget: Decimal | None = None,
        budget_level: str | None = None,
        scenarios: list[str] | None = None,
        target_people: list[str] | None = None,
        max_products: int = 3,
    ) -> list[tuple[ProductCard, dict[str, object]]]:
        cards: list[ProductCard] = []
        candidates: list[tuple[ProductCard, dict[str, object]]] = []
        seen: set[str] = set()
        running_total = Decimal("0")

        for chunk in chunks:
            product_id = str(chunk.get("document_id") or "")
            if not product_id or product_id in seen:
                continue
            product = seed_product_catalog.get_by_id(product_id)
            if not product:
                continue

            if not self._matches_filters(
                product=product,
                budget_level=budget_level,
                scenarios=scenarios,
                target_people=target_people,
            ):
                continue

            card = self.product_to_card(product_id, product)
            if self._exceeds_budget(
                current_total=running_total,
                next_price=card.price,
                budget=budget,
                has_existing_cards=bool(candidates),
            ):
                continue

            seen.add(product_id)
            cards.append(card)
            candidates.append((card, product))
            running_total += card.price or Decimal("0")
            if len(cards) >= max_products:
                break

        return candidates

    def build_semantic_candidates(
        self,
        retrieved_products: list[RetrievedProduct],
        budget: Decimal | None = None,
        max_products: int = 20,
    ) -> list[tuple[ProductCard, dict[str, object]]]:
        candidates: list[tuple[ProductCard, dict[str, object]]] = []
        seen: set[str] = set()
        running_total = Decimal("0")

        for retrieved in retrieved_products:
            product = retrieved.product
            product_id = str(product.get("product_id") or "")
            if not product_id or product_id in seen:
                continue

            card = self.product_to_card(product_id, product)
            if self._exceeds_budget(
                current_total=running_total,
                next_price=card.price,
                budget=budget,
                has_existing_cards=bool(candidates),
            ):
                continue

            seen.add(product_id)
            candidates.append((card, product))
            running_total += card.price or Decimal("0")
            if len(candidates) >= max_products:
                break

        return candidates

    def fallback_products(
        self,
        budget: Decimal | None = None,
        budget_level: str | None = None,
        scenarios: list[str] | None = None,
        target_people: list[str] | None = None,
        max_products: int = 4,
    ) -> list[ProductCard]:
        return [
            card
            for card, _product in self.fallback_candidates(
                budget=budget,
                budget_level=budget_level,
                scenarios=scenarios,
                target_people=target_people,
                max_products=max_products,
            )
        ]

    def fallback_candidates(
        self,
        budget: Decimal | None = None,
        budget_level: str | None = None,
        scenarios: list[str] | None = None,
        target_people: list[str] | None = None,
        max_products: int = 4,
    ) -> list[tuple[ProductCard, dict[str, object]]]:
        candidates: list[tuple[ProductCard, dict[str, object]]] = []
        running_total = Decimal("0")
        for product in seed_product_catalog.list_products():
            product_id = str(product.get("product_id") or "")
            if not product_id:
                continue
            if not self._matches_filters(
                product=product,
                budget_level=budget_level,
                scenarios=scenarios,
                target_people=target_people,
            ):
                continue

            card = self.product_to_card(product_id, product)
            if self._exceeds_budget(
                current_total=running_total,
                next_price=card.price,
                budget=budget,
                has_existing_cards=bool(candidates),
            ):
                continue

            candidates.append((card, product))
            running_total += card.price or Decimal("0")
            if len(candidates) >= max_products:
                break

        return candidates

    @staticmethod
    def product_to_card(product_id: str, product: dict[str, object]) -> ProductCard:
        # 任务 5：优先使用标准化后的 tags / scenarios / target_people / avoid_for
        tags = product.get("tags")
        if not isinstance(tags, list) or not tags:
            tags = product.get("comparison_tags")
        if not isinstance(tags, list) or not tags:
            tags = product.get("use_cases")
        if not isinstance(tags, list):
            tags = []

        highlights = product.get("highlights")
        if not isinstance(highlights, list):
            highlights = []

        scenarios = product.get("scenarios")
        if not isinstance(scenarios, list):
            scenarios = []
        target_people = product.get("target_people")
        if not isinstance(target_people, list):
            target_people = []
        avoid_for = product.get("avoid_for")
        if not isinstance(avoid_for, list):
            avoid_for = []

        return ProductCard(
            product_id=product_id,
            name=str(product.get("name") or ""),
            image_url=str(product.get("image_url") or "") or None,
            price=product.get("price"),
            tags=[str(tag) for tag in tags[:4]],
            highlights=[str(item) for item in highlights[:3]],
            reason=str(highlights[0]) if highlights else "匹配当前送礼需求",
            detail_url=str(product.get("purchase_url") or "") or None,
            scenarios=[str(item) for item in scenarios],
            target_people=[str(item) for item in target_people],
            budget_level=str(product.get("budget_level")) if product.get("budget_level") else None,
            avoid_for=[str(item) for item in avoid_for],
        )

    @staticmethod
    def _build_query(request: RecommendationRequest) -> str:
        return " ".join(
            item
            for item in [
                request.message,
                request.scenario,
                request.preference,
                " ".join(request.scenarios),
                " ".join(request.target_people),
                "组合礼单 送礼 礼物 预算 场景" if request.include_fallback else "送礼 礼物 推荐",
            ]
            if item
        )

    def _rank_candidates(
        self,
        candidates: list[tuple[ProductCard, dict[str, object]]],
        intent: GiftIntent,
    ) -> list[tuple[ProductCard, dict[str, object], ProductScore]]:
        ranked = [
            (card, product, self.product_scorer.score(product, intent))
            for card, product in candidates
        ]
        return sorted(ranked, key=lambda item: item[2].score, reverse=True)

    @staticmethod
    def _merge_candidates(
        candidate_groups: list[list[tuple[ProductCard, dict[str, object]]]],
    ) -> list[tuple[ProductCard, dict[str, object]]]:
        merged: list[tuple[ProductCard, dict[str, object]]] = []
        seen: set[str] = set()
        for group in candidate_groups:
            for card, product in group:
                if card.product_id in seen:
                    continue
                seen.add(card.product_id)
                merged.append((card, product))
        return merged

    async def _resolve_intent(self, request: RecommendationRequest) -> GiftIntent:
        if request.gift_intent is not None:
            return request.gift_intent
        return await self.intent_extractor.extract(request.message)

    @staticmethod
    def _enrich_request(
        request: RecommendationRequest,
        intent: GiftIntent,
    ) -> RecommendationRequest:
        budget = request.budget or intent.budget
        return request.model_copy(
            update={
                "scenario": request.scenario or intent.scenario,
                "budget": budget,
                "preference": request.preference or " ".join(
                    [*intent.preferences, *intent.gift_style]
                )
                or None,
                "scenarios": request.scenarios or intent.scenarios,
                "target_people": request.target_people or intent.target_people,
                "budget_level": request.budget_level or (None if budget is not None else intent.budget_level),
                "gift_intent": intent,
            }
        )

    @staticmethod
    def _exceeds_budget(
        current_total: Decimal,
        next_price: Decimal | None,
        budget: Decimal | None,
        has_existing_cards: bool,
    ) -> bool:
        if not budget or not next_price:
            return False
        if next_price > budget * Decimal("1.15"):
            return True
        if not has_existing_cards:
            return False
        return current_total + next_price > budget * Decimal("1.15")

    # 任务 5 续：target_people 同义词归一表。
    # 商品库里"长辈父母 / 婆婆 / 母亲"等具体词，会被归一化为 IntentExtractor 通用的"长辈 / 父母 / 对象父母"
    # 这样意图侧用通用词、商品侧用具体词时仍能命中。
    _TARGET_PEOPLE_SYNONYMS: dict[str, set[str]] = {
        "长辈父母": {"长辈", "父母", "对象父母"},
        "婆婆": {"长辈", "父母", "对象父母"},
        "岳父": {"长辈", "父母", "对象父母"},
        "岳母": {"长辈", "父母", "对象父母"},
        "母亲": {"长辈", "父母", "对象父母"},
        "父亲": {"长辈", "父母", "对象父母"},
        "女性长辈": {"长辈"},
        "男性长辈": {"长辈"},
        "中老年": {"长辈"},
        "对象父母": {"长辈", "父母"},
        "爱人": {"伴侣"},
        "女朋友": {"伴侣", "爱人", "女生"},
        "男朋友": {"伴侣", "爱人", "男生"},
        "闺蜜": {"朋友", "女生"},
    }

    @classmethod
    def _normalize_people(cls, items: list[str] | set[str]) -> set[str]:
        normalized: set[str] = set()
        for item in items:
            if not isinstance(item, str):
                continue
            normalized.add(item)
            normalized |= cls._TARGET_PEOPLE_SYNONYMS.get(item, set())
        return normalized

    @classmethod
    def _matches_filters(
        cls,
        product: dict[str, object],
        budget_level: str | None,
        scenarios: list[str] | None,
        target_people: list[str] | None,
    ) -> bool:
        # budget_level 精确匹配
        if budget_level:
            if str(product.get("budget_level") or "") != budget_level:
                return False

        # scenarios / target_people 按交集匹配，任一命中即通过
        if scenarios:
            product_scenarios = {
                str(item)
                for item in (product.get("scenarios") or [])
                if isinstance(item, str)
            }
            if not (product_scenarios & set(scenarios)):
                return False

        if target_people:
            product_people_raw = [
                str(item)
                for item in (product.get("target_people") or [])
                if isinstance(item, str)
            ]
            # 商品侧做同义词扩展，意图侧不变；只要扩展后有交集即放行
            if not (cls._normalize_people(product_people_raw) & set(target_people)):
                return False

        return True

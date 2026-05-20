from __future__ import annotations

import json
import logging
import re
from decimal import Decimal
from typing import Any

from app.agent.prompts import (
    GUIDE_SYSTEM_PROMPT,
    RECOMMENDATION_PROMPT_VERSION,
    build_product_rerank_prompt,
)
from app.core.config import settings
from app.llm.client import LLMClient
from app.schemas.gift_intent import GiftIntent
from app.schemas.product import ProductCard
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResult,
    RecommendationStrategy,
)
from app.schemas.recommendation_score import ProductScore
from app.schemas.recommendation_score import RecommendationEvidence
from app.services.budget_optimizer_service import BudgetOptimizerService
from app.services.clarification_service import ClarificationService
from app.services.constraint_relaxation_service import ConstraintRelaxationService
from app.services.intent_extractor import IntentExtractor
from app.services.plan_judge_service import PlanJudgeService
from app.services.product_scorer import ProductScorer
from app.services.retrieval_service import RetrievedProduct, RetrievalService
from app.services.seed_product_loader import seed_product_catalog
from app.services.user_profile_service import UserProfileService

logger = logging.getLogger(__name__)


class RecommendationService:
    """Shared product recommendation utilities for chat and gift-plan flows."""

    def __init__(self) -> None:
        self.retrieval_service = RetrievalService()
        self.clarification_service = ClarificationService()
        self.constraint_relaxation_service = ConstraintRelaxationService()
        self.budget_optimizer_service = BudgetOptimizerService()
        self.plan_judge_service = PlanJudgeService()
        self.intent_extractor = IntentExtractor()
        self.product_scorer = ProductScorer()
        self.user_profiles = UserProfileService()
        self.llm = LLMClient()

    async def recommend_products(self, request: RecommendationRequest) -> RecommendationResult:
        strategy = self._resolve_strategy(request)
        intent = await self._resolve_intent(request)
        profile_key = self._profile_key(request)
        profile = self.user_profiles.get(profile_key) if request.use_profile else None
        disliked_added = self.user_profiles.mark_dislikes_from_message(
            profile_key if request.use_profile else None,
            request.message,
        )
        if request.use_profile:
            profile = self.user_profiles.get(profile_key)
            intent = self.user_profiles.merge_intent(intent, profile)
        enriched = self._enrich_request(request, intent)
        recall_budget = self._recall_budget(intent, enriched.budget)
        if self.clarification_service.should_ask(
            intent,
            allow_generic=enriched.allow_generic_recommendation,
        ):
            question = self.clarification_service.build_question(intent)
            return RecommendationResult(
                products=[],
                citations=[],
                intent=intent,
                needs_clarification=True,
                clarification_question=question,
                missing_slots=intent.missing_slots,
                strategy=strategy,
                pipeline={
                    "strategy": strategy,
                    "needs_clarification": True,
                    "profile_used": bool(profile),
                    "profile_disliked_added": disliked_added,
                    "clarification_slot": intent.missing_slots[0] if intent.missing_slots else "",
                    "returned_count": 0,
                },
            )
        query = self._build_query(enriched)
        retrieval = await self.retrieval_service.hybrid_recall(
            query=query,
            intent=intent,
            top_k=enriched.max_candidates,
        )
        chunks = retrieval.keyword_chunks
        structured_candidates = self.structured_recall_candidates(
            budget=recall_budget,
            budget_level=enriched.budget_level,
            scenarios=enriched.scenarios,
            target_people=enriched.target_people,
            max_candidates=enriched.max_candidates,
        )
        knowledge_candidates = self.build_product_candidates(
            chunks=chunks,
            budget=recall_budget,
            budget_level=enriched.budget_level,
            scenarios=enriched.scenarios,
            target_people=enriched.target_people,
            max_products=enriched.max_candidates,
        )
        semantic_candidates = self.build_semantic_candidates(
            retrieved_products=retrieval.semantic_products,
            budget=recall_budget,
            max_products=enriched.max_candidates,
        )
        candidates = self._merge_candidates(
            [structured_candidates, knowledge_candidates, semantic_candidates]
        )
        profile_filtered_count = 0
        if profile is not None:
            candidates, profile_filtered_count = self._filter_profile_candidates(
                candidates,
                profile.disliked_product_ids,
                profile.recommended_product_ids,
            )

        relaxed_candidates: list[tuple[ProductCard, dict[str, object]]] = []
        if not candidates and (enriched.scenarios or enriched.target_people):
            relaxed_knowledge = self.build_product_candidates(
                chunks=chunks,
                budget=recall_budget,
                budget_level=enriched.budget_level,
                max_products=enriched.max_candidates,
            )
            relaxed_structured = self.structured_recall_candidates(
                budget=recall_budget,
                budget_level=enriched.budget_level,
                max_candidates=enriched.max_candidates,
            )
            relaxed_semantic = self.build_semantic_candidates(
                retrieved_products=retrieval.semantic_products,
                budget=recall_budget,
                max_products=enriched.max_candidates,
            )
            relaxed_candidates = self._merge_candidates(
                [relaxed_knowledge, relaxed_structured, relaxed_semantic]
            )
            if profile is not None:
                relaxed_candidates, profile_filtered_count = self._filter_profile_candidates(
                    relaxed_candidates,
                    profile.disliked_product_ids,
                    profile.recommended_product_ids,
                )
            candidates = relaxed_candidates

        fallback_candidates: list[tuple[ProductCard, dict[str, object]]] = []
        if not candidates and enriched.include_fallback:
            fallback_candidates = self.fallback_candidates(
                budget=recall_budget,
                budget_level=enriched.budget_level,
                scenarios=enriched.scenarios,
                target_people=enriched.target_people,
                max_products=enriched.max_candidates,
            )
            if not fallback_candidates and (enriched.scenarios or enriched.target_people):
                fallback_candidates = self.fallback_candidates(
                    budget=recall_budget,
                    budget_level=enriched.budget_level,
                    max_products=enriched.max_candidates,
                )
            if not fallback_candidates and enriched.budget_level:
                fallback_candidates = self.fallback_candidates(
                    budget=recall_budget,
                    max_products=enriched.max_candidates,
                )
            if profile is not None:
                fallback_candidates, profile_filtered_count = self._filter_profile_candidates(
                    fallback_candidates,
                    profile.disliked_product_ids,
                    profile.recommended_product_ids,
                )
            candidates = fallback_candidates

        ranked_all = self._rank_candidates(candidates, intent)
        rerank_meta: dict[str, int | str | bool] = {
            "llm_rerank_enabled": strategy == "llm_rerank",
            "llm_rerank_used": False,
            "llm_rerank_invalid_count": 0,
            "llm_rerank_fallback": False,
        }
        if strategy == "llm_rerank" and ranked_all:
            ranked_all, rerank_meta = await self._llm_rerank_candidates(
                message=enriched.message,
                intent=intent,
                ranked=ranked_all,
                max_candidates=enriched.max_candidates,
            )
        plans = self.budget_optimizer_service.build_plans(
            ranked=ranked_all,
            max_products=enriched.max_products,
            intent=intent,
        )
        selected_plan = self.plan_judge_service.choose(
            message=enriched.message,
            plans=plans,
        )
        if selected_plan is not None:
            selected_ids = set(selected_plan.product_ids)
            ranked = [item for item in ranked_all if item[0].product_id in selected_ids]
            ranked.sort(key=lambda item: selected_plan.product_ids.index(item[0].product_id))
        else:
            ranked = ranked_all[: enriched.max_products]
        products = [
            card.model_copy(
                update={
                    "reason": score.display_reason or card.reason,
                    "display_reason": score.display_reason or card.reason,
                    "matched_features": score.matched_features,
                    "penalties": score.penalties,
                    "gift_role": (
                        selected_plan.gift_roles.get(card.product_id)
                        if selected_plan is not None
                        else card.gift_role
                    ),
                }
            )
            for card, _, score in ranked
        ]
        evidence = [self._score_to_evidence(score) for _, _, score in ranked]
        self._log_recommendation_evidence(strategy=strategy, evidence=evidence)
        needs_relaxation, relaxation_reason, relaxation_options, suggested_questions = (
            self.constraint_relaxation_service.analyze(
                message=enriched.message,
                intent=intent,
                requested_count=enriched.max_products,
                returned_count=len(ranked),
                candidate_count=len(candidates),
                profile_filtered_count=profile_filtered_count,
                profile_disliked_added=disliked_added,
                top_score=ranked[0][2].score if ranked else None,
            )
        )
        updated_profile = self.user_profiles.update_after_recommendation(
            profile_key if request.use_profile else None,
            intent=intent,
            products=products,
        )

        return RecommendationResult(
            products=products,
            citations=[chunk for chunk in chunks if chunk.get("text")],
            intent=intent,
            needs_clarification=False,
            missing_slots=intent.missing_slots,
            scores=[score for _, _, score in ranked],
            evidence=evidence,
            needs_relaxation=needs_relaxation,
            relaxation_reason=relaxation_reason,
            relaxation_options=relaxation_options,
            suggested_questions=suggested_questions,
            plans=plans,
            selected_plan_id=selected_plan.plan_id if selected_plan else None,
            selected_plan_type=selected_plan.plan_type if selected_plan else None,
            plan_judge_reason=selected_plan.judge_reason if selected_plan else None,
            strategy=strategy,
            pipeline={
                "strategy": strategy,
                "needs_relaxation": needs_relaxation,
                "profile_used": bool(profile or updated_profile),
                "profile_filtered_count": profile_filtered_count,
                "profile_disliked_added": disliked_added,
                "structured_recall_count": len(structured_candidates),
                "knowledge_recall_count": len(knowledge_candidates),
                "semantic_recall_count": len(semantic_candidates),
                "relaxed_recall_count": len(relaxed_candidates),
                "fallback_recall_count": len(fallback_candidates),
                "candidate_count": len(candidates),
                "returned_count": len(ranked),
                "plan_count": len(plans),
                "selected_plan_type": selected_plan.plan_type if selected_plan else None,
                "selected_plan_budget_usage": selected_plan.budget_usage if selected_plan else None,
                "selected_plan_budget_upper_bound": (
                    str(selected_plan.budget_upper_bound) if selected_plan else None
                ),
                "selected_plan_budget_constraint_type": (
                    selected_plan.budget_constraint_type if selected_plan else None
                ),
                "selected_plan_budget_overage_ratio": (
                    selected_plan.budget_overage_ratio if selected_plan else None
                ),
                "selected_plan_objective_score": (
                    selected_plan.objective_score if selected_plan else None
                ),
                **rerank_meta,
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
    def _filter_profile_candidates(
        candidates: list[tuple[ProductCard, dict[str, object]]],
        disliked_product_ids: list[str],
        recommended_product_ids: list[str],
    ) -> tuple[list[tuple[ProductCard, dict[str, object]]], int]:
        excluded = set(disliked_product_ids) | set(recommended_product_ids)
        if not excluded:
            return candidates, 0
        filtered = [item for item in candidates if item[0].product_id not in excluded]
        return filtered, len(candidates) - len(filtered)

    @staticmethod
    def _score_to_evidence(score: ProductScore) -> RecommendationEvidence:
        return RecommendationEvidence(
            product_id=score.product_id,
            score=score.score,
            matched_features=score.matched_features or score.reasons,
            penalties=score.penalties,
            display_reason=score.display_reason,
        )

    @staticmethod
    def _log_recommendation_evidence(
        *,
        strategy: RecommendationStrategy,
        evidence: list[RecommendationEvidence],
    ) -> None:
        logger.debug(
            "recommendation_evidence strategy=%s evidence=%s",
            strategy,
            [
                {
                    "product_id": item.product_id,
                    "score": item.score,
                    "matched_features": item.matched_features,
                    "penalties": item.penalties,
                    "display_reason": item.display_reason,
                }
                for item in evidence
            ],
        )

    async def _llm_rerank_candidates(
        self,
        *,
        message: str,
        intent: GiftIntent,
        ranked: list[tuple[ProductCard, dict[str, object], ProductScore]],
        max_candidates: int,
    ) -> tuple[list[tuple[ProductCard, dict[str, object], ProductScore]], dict[str, int | str | bool]]:
        shortlist = ranked[:max_candidates]
        candidate_payload = [
            {
                "product_id": card.product_id,
                "name": card.name,
                "price": str(card.price) if card.price is not None else None,
                "rule_score": score.score,
                "rule_reasons": score.reasons[:3],
                "penalties": score.penalties[:3],
                "tags": card.tags,
                "highlights": card.highlights,
            }
            for card, _product, score in shortlist
        ]
        prompt = build_product_rerank_prompt(
            message=message,
            intent=intent.model_dump(mode="json"),
            candidates=candidate_payload,
        )
        try:
            result = await self.llm.generate(
                prompt,
                system=GUIDE_SYSTEM_PROMPT,
                temperature=0.1,
                prompt_name="product_rerank",
                prompt_version=RECOMMENDATION_PROMPT_VERSION,
            )
            parsed = self._parse_rerank_json(result.text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_rerank_failed err=%s", exc)
            parsed = None

        if not parsed:
            return ranked, {
                "llm_rerank_enabled": True,
                "llm_rerank_used": False,
                "llm_rerank_invalid_count": 0,
                "llm_rerank_fallback": True,
            }

        allowed_ids = [card.product_id for card, _product, _score in shortlist]
        allowed = set(allowed_ids)
        selected_raw = parsed.get("ranked_product_ids") or []
        selected_ids = [str(item) for item in selected_raw] if isinstance(selected_raw, list) else []
        valid_ids: list[str] = []
        invalid_count = 0
        for product_id in selected_ids:
            if product_id not in allowed:
                invalid_count += 1
                continue
            if product_id not in valid_ids:
                valid_ids.append(product_id)

        if not valid_ids:
            return ranked, {
                "llm_rerank_enabled": True,
                "llm_rerank_used": False,
                "llm_rerank_invalid_count": invalid_count,
                "llm_rerank_fallback": True,
            }

        by_id = {card.product_id: item for item in ranked for card in [item[0]]}
        reordered = [by_id[product_id] for product_id in valid_ids if product_id in by_id]
        reordered.extend(item for item in ranked if item[0].product_id not in valid_ids)
        return reordered, {
            "llm_rerank_enabled": True,
            "llm_rerank_used": True,
            "llm_rerank_invalid_count": invalid_count,
            "llm_rerank_fallback": False,
        }

    @staticmethod
    def _parse_rerank_json(text: str) -> dict[str, Any] | None:
        candidate = (text or "").strip()
        if not candidate:
            return None
        fence = re.match(r"```(?:json)?\s*(.+?)\s*```", candidate, re.DOTALL | re.IGNORECASE)
        if fence:
            candidate = fence.group(1).strip()
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", candidate, re.DOTALL)
            if not match:
                return None
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return data if isinstance(data, dict) else None

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
    def _resolve_strategy(request: RecommendationRequest) -> RecommendationStrategy:
        strategy = request.strategy or settings.recommendation_strategy or "llm_direct"
        if strategy in {"llm_direct", "hybrid_algorithm", "llm_rerank"}:
            return strategy  # type: ignore[return-value]
        return "llm_direct"

    @staticmethod
    def _profile_key(request: RecommendationRequest) -> str | None:
        return request.user_id or request.conversation_id

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
    def _recall_budget(intent: GiftIntent, fallback_budget: Decimal | None) -> Decimal | None:
        upper_bound = intent.budget_upper_bound or fallback_budget
        if upper_bound is None:
            return None
        # Candidate builders already allow 15% overflow for legacy "slightly over budget"
        # behavior. Convert semantic upper bound back to their internal reference budget.
        return (upper_bound / Decimal("1.15")).quantize(Decimal("0.01"))

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

from __future__ import annotations

from decimal import Decimal

from app.schemas.gift_intent import GiftIntent
from app.schemas.recommendation import RelaxationOption


class ConstraintRelaxationService:
    """Suggests negotiation options when recommendation constraints are tight."""

    _NEGATIVE_MARKERS = ("不喜欢", "不想要", "不要这个", "换一个", "换一批", "不合适")

    def analyze(
        self,
        *,
        message: str,
        intent: GiftIntent,
        requested_count: int,
        returned_count: int,
        candidate_count: int,
        profile_filtered_count: int,
        profile_disliked_added: int,
        top_score: float | None,
    ) -> tuple[bool, str | None, list[RelaxationOption], list[str]]:
        negative_feedback = self._is_negative_feedback(message) or profile_disliked_added > 0
        sparse_candidates = returned_count == 0 or (
            returned_count < requested_count and candidate_count <= requested_count
        )
        filtered_heavily = profile_filtered_count >= 2
        weak_top = top_score is not None and top_score < 40

        needs_relaxation = negative_feedback or sparse_candidates or filtered_heavily or weak_top
        if not needs_relaxation:
            return False, None, [], []

        reason = self._build_reason(
            intent=intent,
            returned_count=returned_count,
            profile_filtered_count=profile_filtered_count,
            negative_feedback=negative_feedback,
            weak_top=weak_top,
        )
        options = self._build_options(intent=intent, negative_feedback=negative_feedback)
        questions = self._build_questions(intent=intent, negative_feedback=negative_feedback)
        return True, reason, options, questions

    @classmethod
    def _is_negative_feedback(cls, message: str) -> bool:
        return any(marker in message for marker in cls._NEGATIVE_MARKERS)

    @staticmethod
    def _build_reason(
        *,
        intent: GiftIntent,
        returned_count: int,
        profile_filtered_count: int,
        negative_feedback: bool,
        weak_top: bool,
    ) -> str:
        parts: list[str] = []
        if negative_feedback:
            parts.append("你已经否定过上一批候选，我会避开这些商品")
        if profile_filtered_count:
            parts.append(f"本轮已过滤 {profile_filtered_count} 个重复或不喜欢的商品")
        if returned_count <= 1:
            parts.append("当前约束下可选商品偏少")
        if weak_top:
            parts.append("剩余候选的匹配强度一般")
        if intent.budget is not None:
            parts.append(f"当前预算约为 {intent.budget} 元")
        return "，".join(parts) + "。"

    @staticmethod
    def _build_options(
        *,
        intent: GiftIntent,
        negative_feedback: bool,
    ) -> list[RelaxationOption]:
        options: list[RelaxationOption] = []
        if intent.budget is not None:
            raised = int((intent.budget * Decimal("1.35")).quantize(Decimal("1")))
            options.append(
                RelaxationOption(
                    option_id="raise_budget",
                    label=f"预算放宽到 {raised} 元左右",
                    description="预算小幅上浮后，可以覆盖更精致的礼盒、小家电或轻奢类选择。",
                    patch={"budget": raised},
                )
            )
        options.append(
            RelaxationOption(
                option_id="switch_category",
                label="换成实用类礼物",
                description="保持当前预算，改从咖啡器具、运动健康、数码小配件等实用方向继续找。",
                patch={"preference": "实用 咖啡 运动 健康 数码"},
            )
        )
        if negative_feedback:
            options.append(
                RelaxationOption(
                    option_id="clarify_dislike",
                    label="说明不喜欢的原因",
                    description="告诉我是不喜欢品类、价格、风格还是品牌，我可以更准确地避开。",
                    patch={},
                )
            )
        else:
            options.append(
                RelaxationOption(
                    option_id="clarify_preference",
                    label="补充兴趣偏好",
                    description="补充对方是否喜欢咖啡、运动、香氛、数码或健康类礼物。",
                    patch={},
                )
            )
        if intent.scenario:
            options.append(
                RelaxationOption(
                    option_id="relax_scene",
                    label="放宽场景限制",
                    description=f"不只按“{intent.scenario}”找，也按日常关怀或实用礼物方向补充候选。",
                    patch={"scenario": None},
                )
            )
        return options[:4]

    @staticmethod
    def _build_questions(
        *,
        intent: GiftIntent,
        negative_feedback: bool,
    ) -> list[str]:
        questions: list[str] = []
        if negative_feedback:
            questions.append("你更想避开上一批商品的品类、价格、风格，还是品牌？")
        questions.append("对方更喜欢咖啡、运动、数码、香氛还是健康类礼物？")
        if intent.budget is not None:
            questions.append("预算是否可以小幅放宽 20%-50%，换取更精致的选择？")
        return questions[:3]

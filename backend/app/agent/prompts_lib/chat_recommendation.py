"""聊天推荐场景的用户态 prompt 拼接。

任务 6 续：注入候选商品白名单约束，禁止模型编造不在候选列表里的 product_id / 商品名。
"""

from __future__ import annotations


CHAT_RECOMMENDATION_INSTRUCTION = (
    "回答时优先依据下列知识库片段，并在合适处用 [编号] 标注引用；"
    "如片段中没有相关信息，请明确说明，不要臆测。"
)

CANDIDATE_PRODUCTS_INSTRUCTION = (
    "你只能推荐以下候选商品中的商品；不在列表里的商品名称、product_id、品牌型号都不允许出现。\n"
    "如果你认为列表里的商品都不合适，请直接说明并向用户追问，不要凭空创造商品。\n"
    "推荐时请同时给出商品名称和括号里的 product_id，便于前端对齐展示。\n"
    "推荐理由必须依据每个候选商品的 evidence，不要输出内部分数。"
)

NO_CANDIDATE_PRODUCTS_INSTRUCTION = (
    "当前后端推荐管线没有找到可展示的候选商品。"
    "你不能编造商品名称、product_id、品牌或型号。"
    "请简短说明还需要补充哪些关键信息，或建议用户放宽预算/场景/偏好。"
)

RELAXATION_INSTRUCTION = (
    "后端判断当前约束可能偏紧。请先用温和、协商式语气说明原因，"
    "再给用户 2-3 个可选择的调整方向。不要强迫用户加预算，也不要把放宽选项当作已确认意图。"
)

PLAN_EXPLANATION_INSTRUCTION = (
    "后端已经选择了最终推荐方案。请把它解释成用户能理解的送礼方案："
    "如果有主礼，说明主礼承担核心送礼作用；如果有副礼，说明副礼如何补充主礼。"
    "如果方案总价超过原始预算但未超过预算语义上限，请温和说明这是在用户允许浮动范围内。"
    "不要输出 objective_score、relevance_score 等内部算法分数。"
)


def _format_candidate_products(products: list[dict[str, object]]) -> str:
    lines: list[str] = []
    for item in products:
        name = item.get("name") or ""
        product_id = item.get("product_id") or ""
        price = item.get("price")
        reason = item.get("reason") or ""
        gift_role = item.get("gift_role") or ""
        evidence = item.get("evidence") or item.get("reasons") or []
        penalties = item.get("penalties") or []
        price_text = f"，约 {price} 元" if price not in (None, "") else ""
        reason_text = f"，卖点：{reason}" if reason else ""
        evidence_text = ""
        if isinstance(evidence, list) and evidence:
            evidence_text = "，推荐证据：" + "；".join(str(value) for value in evidence[:3])
        penalty_text = ""
        if isinstance(penalties, list) and penalties:
            penalty_text = "，注意：" + "；".join(str(value) for value in penalties[:2])
        role_text = f"，角色：{gift_role}" if gift_role else ""
        lines.append(
            f"- {name}（product_id: {product_id}）{price_text}{role_text}{reason_text}"
            f"{evidence_text}{penalty_text}"
        )
    return "\n".join(lines)


def _format_selected_plan(selected_plan: dict[str, object]) -> str:
    lines: list[str] = [PLAN_EXPLANATION_INSTRUCTION, "后端已选择推荐方案："]
    field_labels = [
        ("selected_plan_type", "方案类型"),
        ("plan_judge_reason", "裁判理由"),
        ("total_price", "方案总价"),
        ("original_budget", "原始预算"),
        ("budget_upper_bound", "预算语义上限"),
        ("budget_constraint_type", "预算约束类型"),
        ("budget_overage_ratio", "原始预算超出比例"),
    ]
    for key, label in field_labels:
        value = selected_plan.get(key)
        if value not in (None, ""):
            suffix = " 元" if key in {"total_price", "original_budget", "budget_upper_bound"} else ""
            lines.append(f"- {label}：{value}{suffix}")

    gift_roles = selected_plan.get("gift_roles") or {}
    if isinstance(gift_roles, dict) and gift_roles:
        lines.append("- 主副礼角色：")
        for product_id, role in gift_roles.items():
            lines.append(f"  - {product_id}: {role}")
    return "\n".join(lines)


def build_chat_recommendation_prompt(
    message: str,
    chunks: list[dict[str, object]],
    image_hint: str | None = None,
    *,
    candidate_products: list[dict[str, object]] | None = None,
    relaxation: dict[str, object] | None = None,
    selected_plan: dict[str, object] | None = None,
    instruction: str = CHAT_RECOMMENDATION_INSTRUCTION,
) -> str:
    """拼接聊天推荐场景的用户态 prompt。

    Args:
        message: 用户原始消息。
        chunks: 知识库召回片段。
        image_hint: 图片说明（可选）。
        candidate_products: 后端预先用 RecommendationService 算好的候选商品列表，
            每项需至少包含 product_id、name；可选 price、reason。模型只能在此列表内推荐。
        instruction: 知识库引用指令。
    """
    parts: list[str] = []
    if chunks:
        joined = "\n".join(
            f"[{i + 1}] {c.get('text', '')}".strip() for i, c in enumerate(chunks[:5])
        )
        parts.append(instruction + "\n" + joined)

    if candidate_products is not None:
        if not candidate_products:
            parts.append(NO_CANDIDATE_PRODUCTS_INSTRUCTION)
        else:
            parts.append(
                CANDIDATE_PRODUCTS_INSTRUCTION
                + "\n候选商品列表：\n"
                + _format_candidate_products(candidate_products)
            )

    if selected_plan:
        parts.append(_format_selected_plan(selected_plan))

    if relaxation and relaxation.get("needs_relaxation"):
        reason = relaxation.get("reason") or ""
        options = relaxation.get("options") or []
        questions = relaxation.get("suggested_questions") or []
        option_lines: list[str] = []
        if isinstance(options, list):
            for item in options[:4]:
                if not isinstance(item, dict):
                    continue
                label = item.get("label") or ""
                desc = item.get("description") or ""
                option_lines.append(f"- {label}：{desc}")
        question_text = ""
        if isinstance(questions, list) and questions:
            question_text = "\n可追问方向：\n" + "\n".join(f"- {q}" for q in questions[:3])
        parts.append(
            RELAXATION_INSTRUCTION
            + f"\n约束偏紧原因：{reason}"
            + ("\n可选调整方向：\n" + "\n".join(option_lines) if option_lines else "")
            + question_text
        )

    if image_hint:
        parts.append(image_hint)
    parts.append(f"用户问题：{message}")
    return "\n\n".join(parts)

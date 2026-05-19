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


def _format_candidate_products(products: list[dict[str, object]]) -> str:
    lines: list[str] = []
    for item in products:
        name = item.get("name") or ""
        product_id = item.get("product_id") or ""
        price = item.get("price")
        reason = item.get("reason") or ""
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
        lines.append(
            f"- {name}（product_id: {product_id}）{price_text}{reason_text}"
            f"{evidence_text}{penalty_text}"
        )
    return "\n".join(lines)


def build_chat_recommendation_prompt(
    message: str,
    chunks: list[dict[str, object]],
    image_hint: str | None = None,
    *,
    candidate_products: list[dict[str, object]] | None = None,
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

    if image_hint:
        parts.append(image_hint)
    parts.append(f"用户问题：{message}")
    return "\n\n".join(parts)

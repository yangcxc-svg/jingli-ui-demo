"""完整送礼方案 prompt。"""

from __future__ import annotations


GIFT_SOLUTION_JSON_SCHEMA_HINT = """{
  "title": "方案标题",
  "summary": "一句话概括送礼方案",
  "recommendation_reason": "为什么选择这件/这套礼物",
  "giving_timing": "什么时候送更自然",
  "giving_place": "在哪里送更合适",
  "gift_talk": "送礼时可以怎么说",
  "recipient_reaction_reply": "对方推辞或客气时怎么回应",
  "packaging_advice": "包装、卡片或携带建议",
  "avoid_tips": ["送礼时要避开的点"],
  "follow_up_question": "仍需补充时的追问；不需要则为空字符串"
}"""


GIFT_SOLUTION_INSTRUCTION = (
    "请严格输出一个 JSON 对象，不要包裹 Markdown 代码块，不要输出额外文本。"
    "你只能围绕候选商品写方案，不能新增候选商品以外的商品名称、product_id、品牌或型号。"
    "语气要自然、有分寸，避免油腻、夸张或冒犯。"
)


def build_gift_solution_prompt(
    *,
    message: str,
    intent: dict[str, object] | None,
    shape_decision: dict[str, object],
    products: list[dict[str, object]],
    selected_plan: dict[str, object] | None,
) -> str:
    candidate_lines = "\n".join(
        "- {product_id}：{name}，价格 {price} 元，角色 {gift_role}，理由：{reason}".format(
            product_id=item.get("product_id") or "",
            name=item.get("name") or "",
            price=item.get("price") or "",
            gift_role=item.get("gift_role") or "main_gift",
            reason=item.get("reason") or "",
        )
        for item in products
    )
    return (
        "请根据用户送礼需求，生成完整送礼解决方案。\n"
        f"用户需求：{message}\n\n"
        f"结构化意图：{intent or {}}\n\n"
        f"礼物形态判断：{shape_decision}\n\n"
        f"选中方案信息：{selected_plan or {}}\n\n"
        "候选商品白名单：\n"
        f"{candidate_lines or '无候选商品，请不要编造商品，只给出需要补充的信息。'}\n\n"
        "输出必须包含：推荐总结、推荐理由、送礼话术、送礼时机、送礼地点、包装建议、对方推辞回应、避坑提醒。\n"
        + GIFT_SOLUTION_INSTRUCTION
        + "\n\n输出 schema：\n"
        + GIFT_SOLUTION_JSON_SCHEMA_HINT
    )

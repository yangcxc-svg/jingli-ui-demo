"""组合礼单 prompt：要求模型返回结构化 JSON 字段。"""

from __future__ import annotations

from decimal import Decimal


GIFT_PLAN_JSON_SCHEMA_HINT = """{
  "answer": "展示给用户的推荐说明（自然语言，可分段）",
  "selected_product_ids": ["从候选商品中选择的 product_id 列表，必须严格来源于候选商品"],
  "budget_reason": "对预算使用情况的简短说明，预算未明确时可填空字符串",
  "relationship_tone": "对关系分寸的简短说明（如商务、亲密、长辈）",
  "follow_up_question": "如需补充信息可写一个追问；不需要则填空字符串"
}"""


GIFT_PLAN_STRUCTURED_INSTRUCTION = (
    "请严格输出一个 JSON 对象，不要包裹 Markdown 代码块，不要输出任何额外文本。"
    "JSON 结构遵循下方 schema。`selected_product_ids` 必须严格从候选商品中选择，"
    "数量 1~4 件；`answer` 用中文简洁说明组合搭配理由与取舍。"
    "不得新增候选列表以外的商品名称、product_id、品牌或型号。"
    "推荐理由必须依据候选商品的 evidence，不要输出内部分数。"
)


def build_gift_plan_prompt(
    message: str,
    candidate_products: list[dict[str, object]],
    *,
    budget: Decimal | None,
    preference: str | None,
    total_amount: Decimal,
) -> str:
    """拼接组合礼单 prompt，要求模型返回 JSON。

    Args:
        message: 用户需求原文。
        candidate_products: 候选商品列表（每个元素至少包含 product_id/name/price/reason）。
        budget: 用户预算。
        preference: 用户偏好。
        total_amount: 当前组合总价。
    """
    candidate_lines = "\n".join(
        f"- {item.get('product_id')}：{item.get('name')}，价格 {item.get('price')} 元，"
        f"卖点：{item.get('reason') or item.get('highlights') or ''}，"
        f"推荐证据：{';'.join(str(value) for value in (item.get('evidence') or [])[:3])}，"
        f"注意：{';'.join(str(value) for value in (item.get('penalties') or [])[:2])}"
        for item in candidate_products
    )
    budget_line = f"用户预算：{budget} 元。" if budget is not None else "用户未明确预算"
    preference_line = f"用户偏好：{preference}。" if preference else ""
    return (
        "请为用户生成一套组合礼单说明。\n"
        f"用户需求：{message}\n"
        f"{budget_line}\n"
        f"{preference_line}\n"
        f"当前候选组合总价：{total_amount} 元。\n"
        "候选商品：\n"
        f"{candidate_lines or '无候选商品。若无候选商品，请不要编造商品，请输出一个追问或说明暂无合适商品。'}\n\n"
        + GIFT_PLAN_STRUCTURED_INSTRUCTION
        + "\n\n输出 schema：\n"
        + GIFT_PLAN_JSON_SCHEMA_HINT
    )

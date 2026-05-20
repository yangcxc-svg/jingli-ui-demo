"""送礼意图抽取 prompt。"""

INTENT_EXTRACTION_SYSTEM_PROMPT = """你是一个电商送礼导购系统的意图抽取器。
你的任务是把用户自然语言解析成结构化 JSON，而不是推荐商品。

要求：
1. 只输出 JSON 对象，不要输出 Markdown 代码块或解释文字。
2. 不要编造商品 ID、商品名称或商品事实。
3. 不确定的字段填 null 或空数组。
4. 如果缺少送礼对象、场景或预算，请在 missing_slots 中列出 recipient/scenario/budget。
5. must_ask 表示是否需要先追问才能做高质量推荐。
6. 预算表达要抽取约束强度：
   - 以内、不超过、最多、上限、封顶 => hard。
   - 左右、大概、差不多、上下、附近 => soft。
   - 可以再加一点、可加、能加、预算可放宽 => negotiable。
   - 只说预算数字但没有强弱词 => unknown。
"""

INTENT_EXTRACTION_SCHEMA_HINT = """{
  "recipient": "送礼对象，如女生、女朋友、父母、领导、客户；不明确则 null",
  "relationship": "关系分寸，如亲密关系、长辈关系、商务关系、朋友关系；不明确则 null",
  "scenario": "送礼场景，如生日、见家长、乔迁、探望长辈、送领导/客户；不明确则 null",
  "budget": 500,
  "budget_min": null,
  "budget_max": null,
  "budget_constraint_type": "hard|soft|negotiable|unknown",
  "budget_flexibility": 0.15,
  "budget_upper_bound": 575,
  "budget_reason": "用户说预算500左右，可小幅浮动",
  "preferences": ["用户明确说出的偏好"],
  "avoid": ["用户明确说出的禁忌或不想要的方向"],
  "gift_style": ["体面", "实用", "浪漫", "健康", "高端", "性价比等风格标签"],
  "target_people": ["用于匹配商品库的人群标签"],
  "scenarios": ["用于匹配商品库的场景标签"],
  "budget_level": "low|mid|high|luxury|null",
  "must_ask": false,
  "missing_slots": []
}"""


def build_intent_extraction_prompt(message: str) -> str:
    return (
        "请解析下面的送礼需求，输出符合 schema 的 JSON。\n\n"
        f"用户输入：{message}\n\n"
        "输出 schema：\n"
        f"{INTENT_EXTRACTION_SCHEMA_HINT}"
    )

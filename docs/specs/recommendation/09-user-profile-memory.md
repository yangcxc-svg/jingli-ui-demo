# 任务 R9：用户画像与会话记忆

## 目标

让推荐系统能利用用户历史偏好和当前会话上下文。

## 范围

需要实现：

- 会话内记忆：对象、预算、偏好、已推荐商品。
- 简单用户画像：偏好价位、常见送礼对象、偏好风格。
- 推荐时避免重复推荐。

不做：

- 不做复杂账号系统。
- 不做跨设备画像同步。

## 建议数据

```py
class GiftUserProfile(BaseModel):
    preferred_budget_levels: list[str] = []
    preferred_styles: list[str] = []
    frequent_recipients: list[str] = []
    disliked_product_ids: list[str] = []
```

## 验收标准

- 同一会话内追问后能继承预算和对象。
- 已明确不喜欢的商品不会继续推荐。
- 用户画像缺失时不影响推荐。

## 风险点

- 画像不要过早复杂化。
- 本地 Demo 可先用内存或 SQLite 保存。


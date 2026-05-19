# 任务 3：礼单与购物车产品化

## 目标

把当前“加入礼单 + 购物车展示”的 Demo 链路升级成更像真实产品的礼单/结算链路。

## 当前问题

- 礼单存在后端内存里，重启后丢失。
- 购物车已有加减数量、单选、全选和本地合计，但“去结算”还没有调用后端确认。
- 礼单接口已有 `list_id`，但后端实现仍是内存字典，没有持久化。
- 完成任务 1 和任务 2 后，前端页面主要位于 `frontend/src/pages/AppPages.tsx`，礼单 API 位于 `frontend/src/api/giftList.ts`。

## 范围

需要实现：

- 礼单持久化，优先 SQLite。
- 支持商品数量、选中状态、总价计算。
- 支持多个礼单：先保留现有 `list_id` 参数，不新增复杂管理 UI。
- 增加确认结算页或结算摘要区：本轮先实现后端 `checkout-preview`，前端点击“去结算”后展示确认摘要。
- 加入礼单后返回准确数量和总价。

不做：

- 不接真实支付。
- 不做真实库存锁定。
- 不做用户登录体系，除非另起任务。

## 后端建议

新增或完善：

```text
backend/app/models/gift_list.py
backend/app/repositories/gift_list_repo.py
backend/app/services/gift_list_service.py
backend/app/api/routes/gift_list.py
```

建议接口：

- `GET /api/gift-list`
- `POST /api/gift-list/items`
- `PATCH /api/gift-list/items/{product_id}`
- `DELETE /api/gift-list/items/{product_id}`
- `POST /api/gift-list/checkout-preview`

## 本轮实施边界

本轮先完成最小产品化闭环：

- 后端礼单从内存改为 SQLite 持久化。
- 商品以快照 JSON 保存，避免后续商品库变化影响已加入礼单展示。
- 同一商品重复加入时继续沿用当前规则：数量增加。
- 前端购物车点击“去结算”调用 `checkout-preview`，以后端返回金额作为确认口径。
- 前端暂不新增独立路由页面，先在购物车内展示结算确认卡片。

建议新增：

```text
backend/app/repositories/gift_list_repo.py
```

建议调整：

```text
backend/app/core/config.py
backend/app/schemas/gift_list.py
backend/app/services/gift_list_service.py
backend/app/api/routes/gift_list.py
frontend/src/api/giftList.ts
frontend/src/pages/AppPages.tsx
```

## 验收标准

- 后端重启后礼单数据不丢失。
- 加入同一个商品时数量规则明确：增加数量或保持已加入，需要产品侧确认。
- 购物车全选、单选、加减数量、删除都正常。
- 结算摘要只统计被选中的商品，并以后端 `checkout-preview` 返回为准。
- 后端和前端金额显示一致。

## 风险点

- Decimal 金额不要直接用浮点数计算。
- 商品快照需要保存，避免商品库变化后旧礼单无法展示。

## 本轮执行记录

已完成：

- 新增 SQLite 礼单仓储 `backend/app/repositories/gift_list_repo.py`。
- `GiftListService` 已从内存字典改为 SQLite 持久化。
- 新增配置项 `gift_list_db_path`，默认写入 `../storage/gift_list.sqlite3`。
- 新增 `POST /api/gift-list/checkout-preview`。
- 前端 `frontend/src/api/giftList.ts` 新增 `previewGiftListCheckout`。
- 购物车页点击“去结算”后会调用后端结算预览，并在购物车内展示确认摘要。
- `.gitignore` 已忽略 `*.sqlite3`，避免提交本地运行时数据库。

验证结果：

```bash
cd backend
python -m compileall app
```

通过。

```bash
cd frontend
npm run build
```

通过。

使用 FastAPI `TestClient` 手动验证：

- `POST /api/gift-list/items` 返回 200
- `GET /api/gift-list` 返回 200
- `POST /api/gift-list/checkout-preview` 返回 200
- `PATCH /api/gift-list/items/{product_id}` 返回 200
- `DELETE /api/gift-list/items/{product_id}` 返回 200

后续可继续做：

- 增加正式结算提交接口。
- 增加多礼单管理 UI。
- 增加礼单接口自动化测试。

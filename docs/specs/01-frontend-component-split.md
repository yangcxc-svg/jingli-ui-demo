# 任务 1：前端组件拆分

## 目标

把当前接近 2000 行的 `frontend/src/App.tsx` 拆成页面、组件、工具函数和 API 层，降低维护成本，为后续功能迭代打基础。

## 范围

需要拆分：

- 首页和京礼聊天页
- 商品卡片
- 聊天气泡
- 场景按钮
- 组合礼单页面
- 购物车页面
- 通用金额格式化、商品合并等工具函数

不做：

- 不改变现有视觉风格
- 不改变接口协议
- 不新增业务功能

## 建议目录

```text
frontend/src/
  api/
  components/
    chat/
    gift/
    layout/
  pages/
    HomePage.tsx
    JingliPage.tsx
    GiftCartPage.tsx
    GiftComboChatPage.tsx
    GiftComboPlanPage.tsx
    GiftComboPremiumPage.tsx
  data/
    mockHomeData.ts
    giftScenes.ts
  utils/
    money.ts
    products.ts
  App.tsx
```

## 实施步骤

1. 先抽纯展示组件，例如商品卡、聊天气泡、底部导航。
2. 再抽页面组件，保持路由仍在 `App.tsx`。
3. 抽出静态数据，例如首页频道、送礼场景、mock 商品。
4. 抽出工具函数，例如金额格式化、商品去重。
5. 每一步都跑一次前端构建，避免大拆分后难定位问题。

## 验收标准

- `frontend/src/App.tsx` 只负责路由和全局壳层，建议低于 200 行。
- 原有页面路径仍可访问：`/home`、`/jingli`、`/cart`、`/combo-chat`、`/combo-plan`。
- 聊天、加入礼单、购物车加减数量仍可用。
- `npm run build` 通过。

## 风险点

- 拆组件时容易破坏状态传递。
- `navigate`、`giftListCount`、`addedProductIds` 这类状态要明确归属。
- 不要在拆分时顺手改业务逻辑，否则回归成本会变高。


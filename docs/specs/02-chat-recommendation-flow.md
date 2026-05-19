# 任务 2：聊天推荐链路标准化

## 目标

把用户输入、场景按钮、快捷问题统一成一套推荐请求链路，让前端展示和后端调用都可控、可维护。

## 当前问题

- 用户直接输入和场景按钮虽然都能触发推荐，但 prompt 组装散落在页面逻辑中。
- 前端需要同时处理展示文案和真实请求文案。
- 生成中状态、错误状态、商品卡片挂载位置还可以更标准。
- 完成任务 1 第一轮拆分后，当前京礼聊天页位于 `frontend/src/pages/AppPages.tsx`，聊天状态仍然写在页面组件内。

## 范围

需要实现：

- 统一 `sendGiftRequest` 或同类 hook。
- 支持 `displayMessage` 和 `requestMessage` 分离。
- 支持场景、快捷问题、自由输入三种入口。
- 商品卡片只挂在对应的 AI 消息下面。
- 生成失败时显示可重试状态。
- 将聊天请求状态从页面 JSX 中抽到 `frontend/src/hooks/useGiftChat.ts`，让页面只负责渲染和入口事件。

不做：

- 不引入复杂状态管理库，除非后续状态明显失控。
- 不改变后端 SSE 协议，除非任务 4 同时推进。

## 建议前端抽象

```ts
type GiftRequestSource = 'input' | 'scene' | 'quick_question';

interface GiftRequest {
  source: GiftRequestSource;
  displayMessage: string;
  requestMessage: string;
  sceneId?: string;
}
```

## 当前实施落点

建议新增：

```text
frontend/src/hooks/useGiftChat.ts
```

建议调整：

```text
frontend/src/pages/AppPages.tsx
frontend/src/data/giftData.ts
frontend/src/utils/giftFormatting.ts
```

其中 `useGiftChat` 负责：

- 管理 `conversationId`
- 管理 `messages`
- 管理 `isStreaming`
- 管理当前生成中的请求来源
- 处理 SSE 事件
- 失败时记录最后一次请求，提供重试方法

`JingliPage` 负责：

- 把自由输入、场景按钮、快捷问题转换成 `GiftRequest`
- 渲染消息、商品卡片和错误提示
- 管理礼单数量和加入礼单状态

## 验收标准

- 手动输入可以正常流式回复。
- 点击任意场景只让当前场景显示生成中。
- 点击快捷问题也走同一套聊天流。
- AI 回复里的商品卡片和当前回复绑定，不出现固定兜底推荐区。
- 后端异常时用户能看到错误提示，页面不假死。

## 风险点

- SSE 流中商品卡片和文本是分批返回的，前端要用消息 ID 精确更新当前 AI 消息。
- 如果后端返回空商品，前端仍应展示文本，不应报错。

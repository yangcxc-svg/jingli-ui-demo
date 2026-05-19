# 任务 7：测试与质量保障

## 目标

建立最低可用的测试和质量检查，让后续改动不会轻易破坏核心链路。

## 范围

需要实现：

- 后端接口测试。
- 推荐服务单元测试。
- 礼单服务单元测试。
- 前端构建检查。
- 一键验证命令。

不做：

- 暂不追求高覆盖率。
- 暂不引入复杂端到端测试平台，除非项目继续扩大。

## 后端测试建议

覆盖：

- `GET /api/health/ready`
- `POST /api/chat/stream`
- `POST /api/gift-plan/generate`
- `GET/POST/PATCH/DELETE /api/gift-list`

## 前端检查建议

```bash
cd frontend
npm run build
```

后续可增加：

```bash
npm run lint
npm run test
```

## 验收标准

- 后端 `pytest` 能跑通核心接口。
- 前端 `npm run build` 通过。
- README 里有清晰的验证命令。
- 改推荐、礼单、购物车时至少有一个对应测试保护。

## 风险点

- 流式 SSE 测试需要特殊处理，不能只测普通 JSON。
- LLM 真实调用不适合放在默认单测里，应使用 mock。


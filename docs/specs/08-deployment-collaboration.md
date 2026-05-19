# 任务 8：部署与协作标准化

## 目标

让其他开发者 clone 项目后能稳定启动、验证、提交 PR，减少环境问题和协作成本。

## 范围

需要实现：

- 完善 `.env.example`。
- 增加统一启动说明。
- 可选增加 `docker-compose.yml`。
- 清理不应提交的构建产物和缓存。
- 增加 PR checklist。

不做：

- 不直接部署到生产环境。
- 不绑定特定云厂商。

## 建议文件

```text
.gitignore
README.md
docker-compose.yml
docs/development.md
docs/api.md
docs/pr-checklist.md
```

## 标准启动方式

后端：

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 验收标准

- 新开发者按 README 可以启动前后端。
- `.env`、`node_modules`、`dist`、`__pycache__` 不会被提交。
- PR 前有明确检查项：后端启动、前端构建、核心页面手测。
- 如果提供 Docker，`docker compose up` 能启动基础服务。

## 风险点

- 不同机器 Node/Python 版本可能不同，需要在 README 标明推荐版本。
- 真实模型配置不能写进文档示例的真实值。


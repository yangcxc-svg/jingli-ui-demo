# 京礼 AI Demo

这是一个面向移动端体验的 **京礼 AI 送礼推荐 Demo**。用户可以用自然语言描述送礼对象、场景和预算，系统会调用后端 AI 导购能力，基于商品知识库生成推荐文本和商品卡片，并支持把推荐商品加入礼单。

当前项目已经整理成标准前后端结构：

```text
frontend/              前端移动端 UI
backend/               后端 API、AI 导购、知识库检索、礼单接口
storage/sample_docs/   商品知识库种子数据
```

## 技术栈

前端：

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router

后端：

- FastAPI
- Pydantic
- Uvicorn
- SSE 流式响应
- 内存版 RAG/关键词检索
- OpenAI-compatible LLM 调用封装

## Clone 后需要配置什么

后端需要配置模型相关环境变量。项目不会提交真实 `.env`，请复制示例文件：

```bash
cd backend
cp .env.example .env
```

然后编辑 `backend/.env`，至少确认这些配置：

```env
LLM_PROVIDER=你的模型供应商
LLM_MODEL=你的模型名称
LLM_API_KEY=你的 API Key
LLM_BASE_URL=你的模型接口地址
SEED_PRODUCTS_PATH=../storage/sample_docs/seed_products.json
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

如果不配置真实模型，后端会默认走 `mock`，前端会看到 `Mock LLM response.`。

前端默认通过 `/api` 代理到本地后端 `http://localhost:8000`，通常不需要额外配置。需要自定义时可复制：

```bash
cd frontend
cp .env.example .env
```

## 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端健康检查：

```text
http://localhost:8000/api/health/ready
```

礼单接口检查：

```text
http://localhost:8000/api/gift-list
```

## 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://localhost:3000/jingli
```

## 当前已打通的接口

- `POST /api/chat/stream`：流式返回 AI 回复和商品推荐卡片
- `POST /api/gift-plan/generate`：生成结构化组合礼单
- `GET /api/gift-list`：读取当前礼单
- `POST /api/gift-list/items`：把推荐商品加入礼单
- `DELETE /api/gift-list/items/{product_id}`：从礼单移除商品

说明：当前礼单是内存版，重启后端后会清空。后续如果要做正式版本，可以接数据库持久化。

## 常见问题

如果访问 `http://localhost:3000/jingli` 出现 404，通常是前端启动目录错了。请确认是在 `frontend/` 目录执行：

```bash
npm run dev
```

如果 AI 回复是 `Mock LLM response.`，说明后端没有读取到真实模型配置。请检查：

```bash
cd backend
cat .env
```

如果 8000 端口被占用，可以先查进程：

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

再杀掉对应 PID：

```bash
kill <PID>
```

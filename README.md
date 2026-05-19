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

### 如何确认 LLM 是否走真实模型

- 启动后访问 `http://localhost:8000/api/health/ready`，`dependencies.llm` 会返回当前 `provider`、`model`、`is_mock`、`base_url_configured`、`api_key_configured`。
- `is_mock=true` 表示当前是占位模式，前端 AI 回复必然是 `Mock LLM response.`。
- `is_mock=false` 但前端依然看到 mock 响应时，按以下顺序排查：
  1. `cat backend/.env`，确认 `LLM_PROVIDER` 不是 `mock`；
  2. 确认 `LLM_API_KEY` 已填写（Ollama 例外）；
  3. 确认 `LLM_BASE_URL` 与所选 provider 匹配，或留空让后端使用 provider 默认值；
  4. 访问 `http://localhost:8000/api/eval/model-logs?limit=5`，查看最近调用的 `status` 与 `error` 字段，定位是网络、鉴权还是模型名错误；
  5. 修改完 `.env` 后重启 `uvicorn`，配置才会生效。

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

## 如何更新商品数据

商品知识库种子文件位于 `storage/sample_docs/seed_products.json`。后端启动时会按统一 schema 校验，字段不合法会以明确错误终止启动。

商品字段约定（详见 `backend/app/schemas/seed_product.py`）：

- 必填：`product_id`、`name`、`category`
- 推荐填写：`price`（非负数）、`image_url`、`purchase_url`、`brand`、`highlights`
- 推荐过滤字段（任务 5）：
  - `scenarios`：适用送礼场景，如 `["见家长", "生日", "乔迁"]`
  - `target_people`：目标人群，如 `["长辈", "女生", "客户"]`
  - `budget_level`：`low` / `mid` / `high` / `luxury`，未填会按价格自动推导
  - `avoid_for`：不建议送给的人群或情境
  - `tags`：用于展示的标签
- 兼容老字段：`use_cases / target_users / not_recommended_for / comparison_tags`，启动期会自动映射到新字段

更新流程：

1. 编辑 `storage/sample_docs/seed_products.json`，按上面字段补充或新增商品。
2. 本地执行校验（推荐在提交前跑一次）：

```bash
cd backend
python -m app.scripts.validate_products
```

   校验通过会输出 `[ok]` 与商品数量、`budget_level` 分布；任意字段不合法或 `product_id` 重复会以非零状态退出。

3. 重启后端使 `SeedProductCatalog` 重新加载。

如果商品图片不可达，前端 `BackendProductCard` 会自动回退到 🎁 占位图标，不会出现破图。

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

# 图片 URL 策略

## 当前现状（重要）

项目里**没有** `frontend/public/product-images/` 目录。已有 30 件商品的 `image_url` 写的都是 `/product-images/earbuds.jpeg` 这种本地路径，**全部不可达**，前端 `BackendProductCard` 都在走 兜底图标。

也就是说：写不真实的本地路径 **不会**让 UI 报错，只是看不到真实商品图。

## 三种可选策略

### 策略 A：保持现状（推荐 demo 用）

新增商品也用 `/product-images/<品类>.jpeg` 格式占位。

- 优点：与已有 30 件保持一致；schema 校验通过；前端兜底完美工作
- 缺点：所有卡片都是占位图，视觉效果一般

```json
"image_url": "/product-images/tea.jpeg"
```

### 策略 B：用 Unsplash 公开商品图

挑选 [Unsplash](https://unsplash.com) 上的商品类目图（搜 `tea`、`wine`、`fragrance` 等英文关键词），用直接图片 URL：

```json
"image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400"
```

- 优点：真实可见的商品图，UI 立刻好看很多
- 缺点：需要外网访问，断网时仍然兜底；图片可能与具体型号对不上；仅 demo 用途，不可商用

URL 必须以 `https://` 开头，否则 schema 校验报错。

### 策略 C：自己放本地图

提前用 `mkdir -p frontend/public/product-images` 建好目录，把图片放进去：

```json
"image_url": "/product-images/tea-longjing.jpeg"
```

- 优点：完全可控、离线可用
- 缺点：要自己准备图片资产，超出本 skill 范围

## 选择建议

让用户在 Step 1 计划阶段就拍板：

- 想看 UI 效果好不好 -> 策略 B（Unsplash）
- demo 给别人演示，不上线 -> 策略 A（占位 + 兜底）
- 要做正式版本 -> 策略 C（本地图，另起任务准备资产）

## URL 校验注意

`SeedProduct.image_url / purchase_url` 字段会校验 URL 格式，必须满足以下之一：

- `http://...`
- `https://...`
- `/...`（绝对路径）
- `./...`（相对路径）

其他写法（如 `not-a-url`、`example.com`、空字符串）会让启动期校验失败。

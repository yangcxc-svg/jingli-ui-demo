import sys
import subprocess
import nest_asyncio

# 解决在 Jupyter/Colab 中运行 asyncio 的问题
nest_asyncio.apply()

def auto_install_playwright():
    """在代码中自动安装 Playwright 及其浏览器内核"""
    print("检测到未安装 Playwright，正在自动安装，请稍候（可能需要几分钟下载浏览器内核）...")
    try:
        # 1. 安装 Playwright 库 (等同于 pip install playwright)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        print("✔️ Playwright 库安装成功！")

        # 2. 安装 Chromium 浏览器内核 (等同于 playwright install chromium)
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✔️ Chromium 内核安装成功！")

        # 【新增的这一行非常重要，用于安装 Linux 底层缺失的库】
        subprocess.check_call([sys.executable, "-m", "playwright", "install-deps"])
        print("✔️ 系统底层依赖安装成功！")

    except subprocess.CalledProcessError as e:
        print(f"❌ 自动安装失败，请尝试在终端手动执行。错误信息: {e}")
        sys.exit(1)

# 尝试导入 playwright，如果报错则触发自动安装
try:
    from playwright.async_api import async_playwright
except ImportError:
    auto_install_playwright()
    # 安装完成后重新导入
    from playwright.async_api import async_playwright

# 这里继续导入其他需要的库
# from openai import AsyncOpenAI  # 如果 openai 也没安装，也可以用同样的方法处理

import asyncio
import json
import re
from playwright.async_api import async_playwright
from openai import AsyncOpenAI

# 请替换为你自己的 API Key 和对应的 Base URL
OPENAI_API_KEY = "sk-8PupZMgvEDn4dW0SF4iKgGv41EMbklZlTBktwqQYi6PBpNij"

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    # 替换为 PackyAPI 提供的接口地址，注意要带上 /v1
    # 具体的 URL 请以你在 PackyAPI 控制台看到的“接口地址”为准
    base_url="https://www.packyapi.com/v1"
)

async def scrape_jd_product(sku_id: str):
    """
    第一步：使用 Playwright 抓取京东商品的原始非结构化数据
    """
    url = f"https://item.jd.com/{sku_id}.html"
    raw_data = {
        "sku": sku_id,
        "url": url,
        "title": "",
        "price": "",
        "image_url": "",
        "specs": {},
        "raw_text": ""
    }

    print(f"正在抓取商品页面: {url} ...")

    async with async_playwright() as p:
        # 使用 Chromium，并开启一些伪装参数避免被反爬拦截
        # 修改后的代码：添加防崩溃参数
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",               # 必须：在 Linux/Colab 的 root 权限下运行需要此参数
                "--disable-dev-shm-usage",    # 必须：解决部分环境中 Docker/Linux 的内存溢出问题
                "--disable-gpu",              # 可选：禁用 GPU 硬件加速，增加稳定性
                "--disable-blink-features=AutomationControlled" # 可选：顺便加上防爬虫检测
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # 等待网络空闲，确保价格等异步数据加载完成
            # 1. 放宽页面加载的判定条件：只要 DOM 结构加载完就不报错，超时时间加长到 30 秒
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # 2. 显式等待核心元素（商品标题）出现，这是更聪明的等待方式
            await page.wait_for_selector('.sku-name', timeout=10000)

            # 3. 京东的价格是异步加载的，稍微硬性等待 2 秒，让价格请求飞一会儿
            await page.wait_for_timeout(2000)

            # 提取标题
            title_element = await page.query_selector('.sku-name')
            if title_element:
                raw_data["title"] = (await title_element.inner_text()).strip()

            # 提取价格 (京东的价格通常在 .p-price 或 .price 类中)
            price_element = await page.query_selector('.product-price--value')
            print(price_element)
            if price_element:
                raw_data["price"] = (await price_element.inner_text()).strip()

            # 提取主图
            img_element = await page.query_selector('#spec-img')
            if img_element:
                img_src = await img_element.get_attribute('src')
                if img_src:
                    raw_data["image_url"] = "https:" + img_src if img_src.startswith("//") else img_src

            # 提取规格参数表 (Ptable)
            specs = {}
            spec_items = await page.query_selector_all('.Ptable-item')
            for item in spec_items:
                text = await item.inner_text()
                # 简单解析每行文本，例如 "品牌: 迪士尼"
                lines = text.split('\n')
                for line in lines:
                    if '：' in line or ':' in line:
                        parts = re.split(r'：|:', line, 1)
                        if len(parts) == 2:
                            specs[parts[0].strip()] = parts[1].strip()
            raw_data["specs"] = specs

            # 获取页面主要可见文本内容，用于后续 LLM 分析
            body_text = await page.evaluate('document.body.innerText')
            raw_data["raw_text"] = body_text[:3000] # 截取前3000字，避免 Token 超限

        except Exception as e:
            print(f"抓取页面时出错: {e}")
        finally:
            await browser.close()

    return raw_data

async def synthesize_product_data(raw_data: dict) -> dict:
    """
    第二步：使用大语言模型（LLM）将原始数据转换为你要求的复杂结构化 JSON
    """
    print("正在调用 LLM 进行数据清洗和提炼...")

    system_prompt = """
    你是一个专业的数据清洗与电商分析 AI。
    请根据用户提供的【京东商品抓取原始数据】，提取并推断出对应的结构化 JSON 数据。
    必须严格遵循以下 JSON 结构输出，对于原始数据中缺失的信息（如优缺点、使用场景、适用人群、长段落摘要等），请利用你的电商常识进行合理的推理和补全。
    必须返回合法的 JSON 格式，不要包含任何 Markdown 格式符号（如 ```json）如果price为空，根据商品名称设置合理的价格。
    """

    # 将你要求的 JSON 作为示例模板传给模型
    template_json = {
      "product_id": "100327570008",
      "sku": "100327570008",
      "brand": "示例品牌",
      "series": "示例系列",
      "name": "商品全名",
      "model": "商品型号",
      "category": "主分类",
      "subcategory": "子分类",
      "price": "商品价格",
      "currency": "CNY",
      "available_channels": ["京东自营", "京东国际"],
      "purchase_url": "商品链接",
      "image_url": "图片链接",
      "release_date": "年份信息",
      "status": "available",
      "target_users": ["人群1", "人群2"],
      "use_cases": ["场景1", "场景2"],
      "highlights": ["亮点1", "亮点2"],
      "specs": {"属性名": "属性值"},
      "variants": [{"variant_id": "xxx", "name": "xxx", "price_delta": 0, "stock_status": "in_stock"}],
      "pros": ["优点1", "优点2"],
      "cons": ["缺点1", "缺点2"],
      "not_recommended_for": ["不推荐人群1"],
      "comparison_tags": ["标签1", "标签2"],
      "rating": {"score": 5.0, "review_count": 0, "summary": "评价摘要总结"},
      "after_sales": {"warranty": "售后政策", "return_policy": "退换货政策", "service_notes": "服务备注"},
      "source": {"type": "retrieved", "retrieved_at": "2026-05-21", "confidence": "high", "data_sources": ["京东商品详情页"]},
      "knowledge_text": "生成一段流畅、详细的商品百科式介绍（约100-200字）。"
    }

    user_prompt = f"""
    原始抓取数据：
    {json.dumps(raw_data, ensure_ascii=False, indent=2)}

    请严格参照以下 JSON 结构输出：
    {json.dumps(template_json, ensure_ascii=False, indent=2)}
    """

    response = await client.chat.completions.create(
        model="deepseek-v4-flash", # 建议使用能够理解复杂结构和长文本的模型
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8
    )
    print(response)

    result_json = response.choices[0].message.content
    return json.loads(result_json)


import random

async def discover_sku_ids(base_sku: str = "100327570008", max_count: int = 10000) -> list:
    """
    【本地超大任务池矩阵版】：零网络请求！瞬间离线生成 10000+ 级别的高概率有效 SKU
    """
    import random
    sku_ids = []
    print(f"\n⚡ 本地超大矩阵引擎：正在基于种子 【{base_sku}】 离线发散生成 {max_count} 个 SKU 任务池...")

    try:
        base_num = int(base_sku)

        # 1. 核心保障：使用 set 保证去重效率（大数量下 list 的 if not in 速度极慢，会卡死）
        sku_set = {str(base_num)}

        # 2. 动态构建跨度矩阵：混合各种阶梯的跨度，让数字分布在合理的“大、中、小”范围内
        # 既能撞击同店铺，又能跨越到同类目的其他爆款区间
        steps = [
            1, 2, 5, 10, 20, 50,       # 小跨度（同商品多规格/同店铺）
            100, 200, 500, 800,       # 中跨度（同店铺邻近上架）
            1000, 2000, 5000, 10000,   # 大跨度（同行业类目大跳跃）
            50000, 100000, 200000      # 超大跨度（跨品类撞击爆款）
        ]

        # 3. 双向矩阵扩散（核心算法逻辑）
        # 只要数量不够，就在 base_num 的周围进行上下大跨度的加减震荡
        attempts = 0
        max_attempts = max_count * 5 # 防止无限死循环的安全熔断阀门

        while len(sku_set) < max_count and attempts < max_attempts:
            attempts += 1

            # 随机挑一个跨度阶梯
            step = random.choice(steps)
            # 随机决定是往前跳（正）还是往后跳（负）
            direction = random.choice([1, -1])
            # 引入一个大范围的扰动噪声（修复你原本 randint 传多参数报错的问题）
            noise = random.randint(1, 100)

            # 核心计算公式：基于种子，进行大跨度随机发散
            candidate_num = base_num + (direction * (step * noise))

            # 约束 SKU 范围：京东目前的商品 SKU 长度基本在 8 到 12 位纯数字
            if 10000000 <= candidate_num <= 999999999999:
                sku_set.add(str(candidate_num))

        # 4. 极端兜底：如果随机碰撞出来的数量还差一点点，用高效率的线性双向步进补齐
        current_offset = 1
        while len(sku_set) < max_count:
            sku_set.add(str(base_num + current_offset))
            if len(sku_set) < max_count:
                sku_set.add(str(base_num - current_offset))
            current_offset += 1

        # 将 set 转换回 list 返回
        sku_ids = list(sku_set)

        # 打印简短摘要，避免控制台被 10,000 个数字刷屏
        print(f"🎯 本地大矩阵生产成功！零请求，瞬间离线衍生出 {len(sku_ids)} 个 SKU 任务。")
        print(f"📋 任务池前 5 个样品: {sku_ids[:5]} ... 后 5 个样品: {sku_ids[-5:]}")
        return sku_ids

    except Exception as e:
        print(f"⚠️ 本地大矩阵算法异常: {e}")
        # 异常兜底
        local_matrix = ["100327570008", "100068114948", "100062086438", "100115629168", "100083256194"]
        return local_matrix



async def main():
    seed_sku = "100474949533"  # 你的礼物种子（玲娜贝尔）
    max_crawl_limit = 10000

    # 1. 离线生成 10000 个候选池
    sku_tasks = await discover_sku_ids(base_sku=seed_sku, max_count=max_crawl_limit)

    print(f"\n====================== 🟢 泛礼品属性流水线启动 (任务池共 {len(sku_tasks)} 个 SKU) ======================")

    for index, current_sku in enumerate(sku_tasks, start=1):
        # 1. 动态抓取网页原始数据
        raw_scraped_data = await scrape_jd_product(current_sku)

        # 统一转为大写，防止“RTX、PS5、Switch”等英文因为大小写问题漏抓
        title = raw_scraped_data.get("title", "").upper()
        if not title:
            # 网页未分配或已下架，直接跳过
            continue

        # # ⚙️ 【本地字符串多维过滤网】
        # is_gift_material = False

        # # 判定点 A：检查标题中是否命中任何一个泛礼品特征词
        # if any(keyword.upper() in title for keyword in ALL_GIFT_KEYWORDS):
        #     is_gift_material = True

        # # 判定点 B：顺便扫一眼规格参数，有些品类（如奢侈品）可能会标注在参数里
        # if not is_gift_material:
        #     specs_text = json.dumps(raw_scraped_data.get("specs", {}), ensure_ascii=False).upper()
        #     if any(keyword.upper() in specs_text for keyword in ALL_GIFT_KEYWORDS):
        #         is_gift_material = True

        # # 🛑 拦截过滤：如果既没命中品类，也没命中送礼词，判定为日用标品，0毫秒直接丢弃
        # if not is_gift_material:
        #     print(f"⏩ [非礼品拦截] SKU: {current_sku} -> 《{title[:18]}...》不具备送礼属性，直接过滤。")
        #     continue

        # 🎉 成功命中高溢价/送礼属性商品！
        print(f"🔥 [命中高价值商品] SKU: {current_sku} -> 《{title}》 正在送入 DeepSeek-V4 进行深度提炼...")

        # 2.2 传入 DeepSeek-V4 提炼（带有无限重试机制）
        retry_delay = 5
        while True:
            try:
                final_json = await synthesize_product_data(raw_scraped_data)

                print(f"✔️ SKU {current_sku} 数据提炼成功！")

                output_file = f"jd_gift_{current_sku}_data.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(final_json, f, ensure_ascii=False, indent=2)
                print(f"💾 数据已成功自动化导出: {output_file}")
                break

            except Exception as err:
                print(f"❌ LLM 提炼出错: {err}，{retry_delay}秒后重试...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)

        await asyncio.sleep(20) # 顺利完成一个，歇 1 秒继续

    print("\n====================== 🏁 纯本地离线挖掘与数据清洗流水线全部顺利完成！ ======================")

if __name__ == "__main__":
    # 在 Jupyter 等环境中，直接 await 即可
    await main()
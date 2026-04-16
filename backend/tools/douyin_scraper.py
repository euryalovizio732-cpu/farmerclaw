"""
抖音三农爆款数据采集工具
=========================
用 Playwright 无头浏览器抓取抖音网页版搜索结果，获取：
  - 视频标题/文案（选题库 + 口播参考）
  - 用户评论（痛点库）
  - 视频元数据（播放量/点赞量）

使用前先安装依赖：
  pip install playwright httpx
  playwright install chromium

运行方式：
  python -m tools.douyin_scraper --keyword "赣南脐橙" --max-videos 20
  python -m tools.douyin_scraper --keyword "丹东草莓 产地直发" --max-videos 30
  python -m tools.douyin_scraper --keyword "蓝莓 直播" --max-videos 20 --with-comments
"""

import asyncio
import argparse
import json
import os
import sys
import time
import random
from pathlib import Path
from datetime import datetime

# ─── 输出目录 ───
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "douyin_raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def scrape_douyin_search(keyword: str, max_videos: int = 20, with_comments: bool = False):
    """
    双策略采集：
      策略A（优先）: Playwright 打开浏览器，用户手动过验证码后自动采集
      策略B（兜底）: 直接提取 SSR 页面 meta 数据
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ 请先安装 Playwright：")
        print("   pip install playwright && playwright install chromium")
        sys.exit(1)

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page = await context.new_page()

        print(f"🔍 正在搜索：{keyword}")
        print(f"📊 目标数量：{max_videos} 条视频")
        print()

        # ─── 步骤1：打开搜索页 ───
        search_url = f"https://www.douyin.com/search/{keyword}?type=video"
        try:
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
        except Exception:
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e2:
                print(f"⚠️ 页面打开异常: {e2}")

        # ─── 步骤2：等用户过验证码（如果有）───
        print()
        print("=" * 50)
        print("👀 浏览器已打开！请查看桌面上的 Chromium 窗口：")
        print("   - 如果看到搜索结果 → 脚本会自动继续")
        print("   - 如果看到验证码 → 请手动完成滑块验证")
        print("   - 如果要求登录 → 用手机扫码登录即可")
        print("=" * 50)
        print()

        found_content = False
        for wait_i in range(120):  # 最多等2分钟
            try:
                count = await page.evaluate("""
                    () => {
                        // 方式1：搜索结果中的视频链接
                        const videoLinks = document.querySelectorAll('a[href*="/video/"]');
                        if (videoLinks.length > 0) return videoLinks.length;
                        // 方式2：搜索结果列表
                        const items = document.querySelectorAll('[data-e2e="scroll-list"] li, ul[class*="list"] li');
                        return items.length;
                    }
                """)
                if count > 0:
                    print(f"\n✅ 检测到 {count} 个搜索结果！开始采集...")
                    found_content = True
                    break
            except Exception:
                pass

            if wait_i % 5 == 0:
                print(f"   ⏳ 等待页面内容加载... ({wait_i}s)")
            await asyncio.sleep(1)

        if not found_content:
            print("\n⚠️ 超时。尝试从当前页面提取已有内容...")

        # ─── 步骤3：滚动加载更多 ───
        for scroll_i in range(20):
            try:
                current = await page.evaluate(
                    "() => document.querySelectorAll('a[href*=\"/video/\"]').length"
                )
            except Exception:
                current = 0

            if current >= max_videos:
                break

            print(f"\r   滚动加载中... 已有 {current}/{max_videos}", end="", flush=True)
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            except Exception:
                pass
            await asyncio.sleep(random.uniform(2, 4))

        print()

        # ─── 步骤4：提取所有视频链接 ───
        try:
            video_links = await page.evaluate("""
                () => {
                    const seen = new Set();
                    const links = [];
                    for (const a of document.querySelectorAll('a[href*="/video/"]')) {
                        let href = a.href || a.getAttribute('href') || '';
                        if (!href.includes('/video/')) continue;
                        if (!href.startsWith('http')) href = 'https://www.douyin.com' + href;
                        if (!seen.has(href)) { seen.add(href); links.push(href); }
                    }
                    return links;
                }
            """)
        except Exception:
            video_links = []

        video_links = video_links[:max_videos]
        print(f"🔗 提取到 {len(video_links)} 个视频链接")

        if not video_links:
            # 兜底：尝试从页面 SSR 数据中提取
            print("🔄 尝试从页面数据中直接提取...")
            try:
                ssr_data = await page.evaluate("""
                    () => {
                        // 抖音SSR会把数据注入到 window.__INITIAL_STATE__ 或 script 标签
                        const scripts = document.querySelectorAll('script');
                        for (const s of scripts) {
                            const text = s.textContent || '';
                            if (text.includes('desc') && text.includes('video') && text.length > 500) {
                                return text.substring(0, 50000);
                            }
                        }
                        // 也尝试 RENDER_DATA
                        const renderEl = document.getElementById('RENDER_DATA');
                        if (renderEl) return decodeURIComponent(renderEl.textContent);
                        return '';
                    }
                """)
                if ssr_data:
                    print(f"   📦 获取到 SSR 数据 ({len(ssr_data)} 字符)，正在解析...")
                    results = _parse_ssr_data(ssr_data, keyword)
                    if results:
                        print(f"   ✅ 从 SSR 数据中解析出 {len(results)} 条视频！")
            except Exception as e:
                print(f"   ⚠️ SSR 提取失败: {e}")

        # ─── 步骤5：逐个访问视频页提取详情 ───
        for i, link in enumerate(video_links):
            try:
                print(f"\n📹 [{i+1}/{len(video_links)}] {link}")
                await page.goto(link, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(random.uniform(2, 4))

                video_data = await page.evaluate("""
                    () => {
                        const d = { desc: '', author: '', likes: '', comments_count: '', meta_desc: '' };
                        // 描述（多种选择器）
                        for (const sel of ['[data-e2e="video-desc"]', '[class*="title"]', 'h1', '[class*="desc"]']) {
                            const el = document.querySelector(sel);
                            if (el && el.innerText.trim().length > 5) { d.desc = el.innerText.trim(); break; }
                        }
                        // meta description（通常包含完整文案）
                        const meta = document.querySelector('meta[name="description"]');
                        if (meta) d.meta_desc = meta.getAttribute('content') || '';
                        // 作者
                        for (const sel of ['[data-e2e="video-author"]', '[class*="author"] span', '[class*="nickname"]']) {
                            const el = document.querySelector(sel);
                            if (el) { d.author = el.innerText.trim(); break; }
                        }
                        // 互动数据
                        const likeEl = document.querySelector('[data-e2e="video-like-count"]');
                        if (likeEl) d.likes = likeEl.innerText.trim();
                        const cmtEl = document.querySelector('[data-e2e="video-comment-count"]');
                        if (cmtEl) d.comments_count = cmtEl.innerText.trim();
                        return d;
                    }
                """)

                # 取更长的描述
                desc = video_data.get("desc", "")
                meta_desc = video_data.get("meta_desc", "")
                final_desc = meta_desc if len(meta_desc) > len(desc) else desc

                record = {
                    "desc": final_desc,
                    "author": video_data.get("author", ""),
                    "likes": video_data.get("likes", ""),
                    "comments_count": video_data.get("comments_count", ""),
                    "url": link,
                    "keyword": keyword,
                    "scraped_at": datetime.now().isoformat(),
                }

                # 可选：抓评论
                if with_comments:
                    comments = await _extract_comments(page)
                    record["comments"] = comments
                    print(f"   💬 {len(comments)} 条评论")

                results.append(record)
                print(f"   ✅ {final_desc[:60]}...")
                print(f"   👍 {video_data.get('likes', '-')}  💬 {video_data.get('comments_count', '-')}  @{video_data.get('author', '-')}")

            except Exception as e:
                print(f"   ⚠️ 失败: {e}")
            await asyncio.sleep(random.uniform(2, 5))

        await browser.close()

    return results


def _parse_ssr_data(raw: str, keyword: str) -> list[dict]:
    """从抖音 SSR/RENDER_DATA 中解析视频数据"""
    results = []
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # 尝试从文本中找 JSON 对象
        import re
        matches = re.findall(r'\{[^{}]{50,}\}', raw)
        for m in matches:
            try:
                obj = json.loads(m)
                if "desc" in obj:
                    results.append({
                        "desc": obj.get("desc", ""),
                        "author": obj.get("nickname", obj.get("author", "")),
                        "likes": str(obj.get("digg_count", "")),
                        "comments_count": str(obj.get("comment_count", "")),
                        "url": f"https://www.douyin.com/video/{obj.get('aweme_id', '')}",
                        "keyword": keyword,
                        "scraped_at": datetime.now().isoformat(),
                    })
            except Exception:
                continue
        return results

    # 递归搜索包含视频数据的节点
    def _walk(node, depth=0):
        if depth > 10:
            return
        if isinstance(node, dict):
            if "desc" in node and ("aweme_id" in node or "video" in node):
                results.append({
                    "desc": node.get("desc", ""),
                    "author": node.get("author", {}).get("nickname", "") if isinstance(node.get("author"), dict) else str(node.get("nickname", "")),
                    "likes": str(node.get("statistics", {}).get("digg_count", node.get("digg_count", ""))),
                    "comments_count": str(node.get("statistics", {}).get("comment_count", node.get("comment_count", ""))),
                    "url": f"https://www.douyin.com/video/{node.get('aweme_id', '')}",
                    "keyword": keyword,
                    "scraped_at": datetime.now().isoformat(),
                })
            for v in node.values():
                _walk(v, depth + 1)
        elif isinstance(node, list):
            for item in node:
                _walk(item, depth + 1)

    _walk(data)
    return results


async def _extract_comments(page, max_comments: int = 20) -> list[str]:
    """提取视频评论"""
    comments = []
    try:
        await asyncio.sleep(2)
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(1)
        comment_els = await page.query_selector_all(
            '[data-e2e="comment-list"] [class*="comment-content"], '
            '[class*="comment-item"] p, [class*="commentContent"]'
        )
        for el in comment_els[:max_comments]:
            text = await el.inner_text()
            if text.strip():
                comments.append(text.strip())
    except Exception as e:
        print(f"   ⚠️ 评论抓取异常: {e}")
    return comments


def save_results(results: list[dict], keyword: str):
    """保存抓取结果"""
    if not results:
        print("\n❌ 没有抓到任何数据")
        return

    # 保存 JSON 原始数据
    safe_kw = keyword.replace(" ", "_").replace("/", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"{safe_kw}_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 原始数据已保存: {json_path}")

    # 生成可直接粘贴到 sample_library.py 的代码片段
    snippet_path = OUTPUT_DIR / f"{safe_kw}_{ts}_snippets.py"
    with open(snippet_path, "w", encoding="utf-8") as f:
        f.write(f'# 抖音采集数据 - 关键词: {keyword}\n')
        f.write(f'# 采集时间: {datetime.now().isoformat()}\n')
        f.write(f'# 数据量: {len(results)} 条\n')
        f.write(f'# 用法：复制下面的 dict 到 sample_library.py 对应品类的 script/topic 列表中\n\n')

        for i, r in enumerate(results):
            desc = (r.get("desc") or r.get("title", "")).replace('"', '\\"').replace("\n", " ")
            author = r.get("author", "未知")
            likes = r.get("likes", "0")
            url = r.get("url", "")

            f.write(f'# ── 样本 {i+1} ──\n')
            f.write('{\n')
            f.write(f'    "script": "{desc}",\n')
            f.write(f'    "hook_type": "待分类",  # 人工标注: 知识反问/价格冲击/产地溯源/季节稀缺/情绪共鸣\n')
            f.write(f'    "source": "抖音@{author} {url}",\n')
            f.write(f'    "views_approx": 0,  # 点赞: {likes}\n')
            f.write(f'    "usable_direct": False,  # 需人工审核后改为 True\n')
            f.write('},\n\n')

        # 评论数据（如果有）
        all_comments = []
        for r in results:
            all_comments.extend(r.get("comments", []))
        if all_comments:
            f.write(f'\n# ═══ 用户评论（痛点库原始数据）═══\n')
            f.write(f'# 共 {len(all_comments)} 条\n')
            f.write('SCRAPED_COMMENTS = [\n')
            for c in all_comments:
                c_escaped = c.replace('"', '\\"').replace("\n", " ")
                f.write(f'    "{c_escaped}",\n')
            f.write(']\n')

    print(f"📋 代码片段已生成: {snippet_path}")
    print(f"   → 复制到 sample_library.py 对应品类即可使用")

    # 统计摘要
    print(f"\n{'='*50}")
    print(f"📊 采集摘要")
    print(f"{'='*50}")
    print(f"   关键词: {keyword}")
    print(f"   视频数: {len(results)}")
    all_comments = [c for r in results for c in r.get("comments", [])]
    if all_comments:
        print(f"   评论数: {len(all_comments)}")
    print(f"   输出: {json_path}")
    print(f"   代码: {snippet_path}")


def main():
    parser = argparse.ArgumentParser(description="抖音三农爆款数据采集工具")
    parser.add_argument("--keyword", "-k", required=True, help="搜索关键词，如'赣南脐橙'")
    parser.add_argument("--max-videos", "-n", type=int, default=20, help="最大抓取视频数（默认20）")
    parser.add_argument("--with-comments", "-c", action="store_true", help="同时抓取评论")
    parser.add_argument("--headless", action="store_true", help="无头模式（后台运行，可能触发验证）")

    args = parser.parse_args()

    print("=" * 50)
    print("🌾 抖音三农爆款数据采集工具")
    print("=" * 50)
    print()

    results = asyncio.run(
        scrape_douyin_search(
            keyword=args.keyword,
            max_videos=args.max_videos,
            with_comments=args.with_comments,
        )
    )

    save_results(results, args.keyword)


# ─── 批量采集预设关键词 ───
PRESET_KEYWORDS = [
    "赣南脐橙 产地直发",
    "丹东草莓 直播",
    "蓝莓 产地 鲜果",
    "阳山水蜜桃",
    "烟台樱桃 产地",
    "麻阳冰糖橙",
    "海南芒果 产地直发",
    "大凉山苹果",
    "新疆阿克苏苹果",
    "秭归脐橙 产地",
]


async def batch_scrape(max_per_keyword: int = 10):
    """批量采集所有预设关键词"""
    print("🚀 启动批量采集模式")
    print(f"   共 {len(PRESET_KEYWORDS)} 个关键词，每个抓 {max_per_keyword} 条\n")

    all_results = {}
    for i, kw in enumerate(PRESET_KEYWORDS):
        print(f"\n{'='*50}")
        print(f"[{i+1}/{len(PRESET_KEYWORDS)}] 关键词: {kw}")
        print(f"{'='*50}")

        try:
            results = await scrape_douyin_search(kw, max_videos=max_per_keyword)
            all_results[kw] = results
            save_results(results, kw)
        except Exception as e:
            print(f"⚠️ {kw} 采集失败: {e}")

        # 关键词间隔
        if i < len(PRESET_KEYWORDS) - 1:
            wait = random.uniform(10, 20)
            print(f"\n⏳ 等待 {wait:.0f} 秒后继续...")
            await asyncio.sleep(wait)

    print(f"\n🎉 批量采集完成！共处理 {len(PRESET_KEYWORDS)} 个关键词")
    total = sum(len(v) for v in all_results.values())
    print(f"   总计获取 {total} 条视频数据")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        asyncio.run(batch_scrape())
    else:
        main()

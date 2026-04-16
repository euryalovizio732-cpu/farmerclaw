"""公开文章爬虫 — 从搜狐/百家号/头条抓取三农直播话术文章

目标：抓取包含真实口播稿/直播话术/选题标题的公开文章
用途：
  - 从文章中提取完整口播稿原文 → 口播稿样本库
  - 从文章中提取直播话术模块 → 直播话术样本库
  - 从文章中提取选题标题 → 选题样本库

使用方式：
  python scripts/scrape_articles.py

输出：
  scripts/output/articles_raw.json
"""

import json
import time
import random
import re
import os
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ── 搜索关键词 ──
SEARCH_QUERIES = [
    "农产品直播话术 口播稿",
    "水果直播带货话术模板",
    "脐橙直播话术 完整文案",
    "三农直播话术 开场白 逼单",
    "农产品短视频口播 文案",
    "直播卖水果 话术脚本",
    "草莓直播话术 坏果包赔",
    "苹果直播 产地直发 话术",
    "芒果直播带货 口播",
    "抖音三农 选题标题 爆款",
]


def search_sogou(query: str, page: int = 1) -> list[dict]:
    """通过搜狗搜索获取文章URL列表"""
    url = "https://www.sogou.com/web"
    params = {"query": query, "page": page}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for item in soup.select(".vrwrap, .rb"):
            link = item.select_one("a[href]")
            if link:
                href = link.get("href", "")
                title = link.get_text(strip=True)
                if title and href:
                    results.append({"title": title, "url": href})

        return results[:10]
    except Exception as e:
        print(f"  搜索失败: {query} - {e}")
        return []


def search_bing(query: str) -> list[dict]:
    """通过Bing搜索获取文章URL列表"""
    url = "https://cn.bing.com/search"
    params = {"q": query, "cc": "cn"}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for item in soup.select("li.b_algo"):
            link = item.select_one("h2 a[href]")
            if link:
                href = link.get("href", "")
                title = link.get_text(strip=True)
                if title and href and "http" in href:
                    results.append({"title": title, "url": href})

        return results[:10]
    except Exception as e:
        print(f"  Bing搜索失败: {query} - {e}")
        return []


def fetch_article(url: str) -> dict:
    """抓取单篇文章内容"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 移除script/style
        for tag in soup.select("script, style, nav, footer, header"):
            tag.decompose()

        # 提取正文
        # 搜狐
        article = soup.select_one("article") or soup.select_one(".article-content")
        if not article:
            # 通用：找最长的文本块
            article = soup.select_one("main") or soup.select_one(".content") or soup.body

        if not article:
            return {"url": url, "text": "", "title": ""}

        text = article.get_text(separator="\n", strip=True)
        title = soup.title.get_text(strip=True) if soup.title else ""

        return {"url": url, "title": title, "text": text}

    except Exception as e:
        print(f"  抓取文章失败: {url} - {e}")
        return {"url": url, "text": "", "title": ""}


def extract_scripts_from_text(text: str) -> list[str]:
    """从文章文本中提取看起来像口播稿/话术的段落

    规则（只提取，不生成）：
    - 包含引号的对话文本
    - 包含"家人""宝贝""直播间""下单""包赔"等关键词的段落
    - 长度在30-500字之间
    """
    keywords = [
        "家人", "宝贝", "直播间", "下单", "包赔", "产地", "发货",
        "点关注", "小黄车", "链接", "扣1", "包邮", "坏果",
        "现摘", "新鲜", "试吃", "秒杀", "福利", "库存",
        "逼单", "催单", "开场", "话术",
    ]

    scripts = []
    paragraphs = text.split("\n")

    for para in paragraphs:
        para = para.strip()
        if len(para) < 30 or len(para) > 500:
            continue

        # 至少命中2个关键词才算话术
        hit_count = sum(1 for kw in keywords if kw in para)
        if hit_count >= 2:
            # 清理：去掉明显非话术的段落
            if any(skip in para for skip in ["版权", "转载", "关注公众号", "微信扫码", "下载APP"]):
                continue
            scripts.append(para)

    # 也提取引号中的文本
    quoted = re.findall(r'[""「」](.{20,300}?)[""「」]', text)
    for q in quoted:
        hit_count = sum(1 for kw in keywords if kw in q)
        if hit_count >= 1:
            scripts.append(q)

    return list(set(scripts))


def main():
    print("=" * 60)
    print("公开文章爬虫 — 采集三农直播话术")
    print("=" * 60)

    all_articles = []
    all_scripts = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        print(f"\n搜索: {query}")

        # Bing搜索
        results = search_bing(query)
        print(f"  找到 {len(results)} 个结果")

        for r in results:
            if r["url"] in seen_urls:
                continue
            seen_urls.add(r["url"])

            print(f"  抓取: {r['title'][:40]}...")
            article = fetch_article(r["url"])

            if article["text"] and len(article["text"]) > 100:
                all_articles.append(article)

                # 提取话术
                scripts = extract_scripts_from_text(article["text"])
                for s in scripts:
                    all_scripts.append({
                        "script": s,
                        "source_url": r["url"],
                        "source_title": r["title"],
                        "search_query": query,
                    })
                if scripts:
                    print(f"    提取到 {len(scripts)} 条话术")

            time.sleep(random.uniform(1.5, 3.0))

        time.sleep(random.uniform(2.0, 4.0))

    # 保存原始文章
    articles_file = os.path.join(OUTPUT_DIR, "articles_raw.json")
    with open(articles_file, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    # 保存提取的话术
    scripts_file = os.path.join(OUTPUT_DIR, "extracted_scripts.json")
    with open(scripts_file, "w", encoding="utf-8") as f:
        json.dump(all_scripts, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"采集完成！")
    print(f"  文章: {len(all_articles)}篇 → {articles_file}")
    print(f"  话术: {len(all_scripts)}条 → {scripts_file}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

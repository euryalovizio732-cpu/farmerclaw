"""京东商品评论爬虫 — 抓取水果品类真实差评/好评

目标：抓取京东水果商品的真实用户评论，用于：
  - 痛点样本库（差评）
  - 回复话术参考（商家回复）
  - 卖点提炼参考（好评中的高频词）

使用方式：
  python scripts/scrape_jd_reviews.py

输出：
  scripts/output/jd_reviews.json
"""

import json
import time
import random
import os
import requests

# ── 配置 ──
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 品类搜索关键词 → 从京东搜索页自动获取真实商品ID
CATEGORY_SEARCH = {
    "脐橙": "赣南脐橙",
    "苹果": "烟台苹果",
    "草莓": "丹东草莓",
    "芒果": "海南芒果",
    "葡萄": "阳光玫瑰葡萄",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://item.jd.com/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def search_jd_products(keyword: str, max_count: int = 3) -> list[str]:
    """从京东搜索页获取真实商品ID"""
    from bs4 import BeautifulSoup
    url = "https://search.jd.com/Search"
    params = {"keyword": keyword, "enc": "utf-8"}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        ids = []
        for li in soup.select("li.gl-item[data-sku]"):
            sku = li.get("data-sku", "")
            if sku and sku.isdigit():
                ids.append(sku)
                if len(ids) >= max_count:
                    break
        print(f"  搜索'{keyword}' 获取到{len(ids)}个商品ID: {ids}")
        return ids
    except Exception as e:
        print(f"  搜索京东失败: {keyword} - {e}")
        return []


def fetch_jd_comments(product_id: str, page: int = 0, score: int = 0) -> list[dict]:
    """
    抓取京东商品评论

    Args:
        product_id: 商品ID
        page: 页码（0开始）
        score: 0=全部, 1=差评, 2=中评, 3=好评

    Returns:
        评论列表
    """
    url = "https://club.jd.com/comment/productPageComments.action"
    params = {
        "callback": "fetchJSON_comment98",
        "productId": product_id,
        "score": score,
        "sortType": 5,  # 按时间排序
        "page": page,
        "pageSize": 10,
        "isShadowSku": 0,
        "fold": 1,
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        # 去掉JSONP包装
        text = resp.text
        if text.startswith("fetchJSON_comment98("):
            text = text[len("fetchJSON_comment98("):-2]

        data = json.loads(text)
        comments = data.get("comments", [])

        results = []
        for c in comments:
            results.append({
                "content": c.get("content", ""),
                "score": c.get("score", 0),
                "creation_time": c.get("creationTime", ""),
                "reply": c.get("reply", {}).get("content", "") if c.get("reply") else "",
                "product_name": c.get("referenceName", ""),
                "user_level": c.get("userLevelName", ""),
                "image_count": len(c.get("images", [])),
            })
        return results

    except Exception as e:
        print(f"  抓取失败 product_id={product_id} page={page}: {e}")
        return []


def scrape_category(category: str, product_ids: list[str], pages_per_product: int = 5):
    """抓取一个品类下所有商品的评论"""
    all_reviews = []

    for pid in product_ids:
        print(f"\n  抓取 [{category}] 商品ID: {pid}")

        # 抓差评（score=1）
        for page in range(pages_per_product):
            reviews = fetch_jd_comments(pid, page=page, score=1)
            if not reviews:
                break
            for r in reviews:
                r["category"] = category
                r["source"] = f"京东商品评论 商品ID:{pid}"
                r["review_type"] = "差评"
            all_reviews.extend(reviews)
            print(f"    差评 page={page}: {len(reviews)}条")
            time.sleep(random.uniform(1.5, 3.0))

        # 抓好评（score=3）— 用于提炼卖点
        for page in range(min(2, pages_per_product)):
            reviews = fetch_jd_comments(pid, page=page, score=3)
            if not reviews:
                break
            for r in reviews:
                r["category"] = category
                r["source"] = f"京东商品评论 商品ID:{pid}"
                r["review_type"] = "好评"
            all_reviews.extend(reviews)
            print(f"    好评 page={page}: {len(reviews)}条")
            time.sleep(random.uniform(1.5, 3.0))

    return all_reviews


def main():
    print("=" * 60)
    print("京东水果评论爬虫 — 采集真实用户评论")
    print("=" * 60)

    all_data = []

    for category, search_kw in CATEGORY_SEARCH.items():
        pids = search_jd_products(search_kw)
        if not pids:
            print(f"  [{category}] 未获取到商品ID，跳过")
            continue
        time.sleep(random.uniform(1.5, 3.0))
        print(f"\n{'─' * 40}")
        print(f"品类: {category} ({len(pids)}个商品) IDs: {pids}")
        print(f"{'─' * 40}")

        reviews = scrape_category(category, pids)
        all_data.extend(reviews)
        print(f"  [{category}] 总计: {len(reviews)}条")

        # 品类之间间隔
        time.sleep(random.uniform(2.0, 4.0))

    # 保存结果
    output_file = os.path.join(OUTPUT_DIR, "jd_reviews.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # 统计
    bad_reviews = [r for r in all_data if r["review_type"] == "差评"]
    good_reviews = [r for r in all_data if r["review_type"] == "好评"]

    print(f"\n{'=' * 60}")
    print(f"采集完成！")
    print(f"  总计: {len(all_data)}条评论")
    print(f"  差评: {len(bad_reviews)}条（用于痛点库）")
    print(f"  好评: {len(good_reviews)}条（用于卖点提炼）")
    print(f"  保存: {output_file}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

"""抖音视频标题爬虫 — 抓取三农品类真实爆款视频标题

目标：通过抖音网页版搜索，抓取水果品类热门视频标题
用途：选题标题样本库

使用方式：
  python scripts/scrape_dy_titles.py

输出：
  scripts/output/dy_titles.json

注意：抖音反爬较强，如果失败可以手动从抖音搜索页复制
"""

import json
import time
import random
import os
import requests

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.douyin.com/",
    "Accept": "application/json",
    "Cookie": "",  # 需要填入你的抖音Cookie
}

# 搜索关键词
SEARCH_KEYWORDS = [
    "赣南脐橙 产地直发",
    "草莓 坏果包赔",
    "苹果 产地直发",
    "芒果 包甜",
    "葡萄 阳光玫瑰",
    "水果 助农",
    "三农 水果",
    "农产品 直播",
    "大米 产地",
    "蔬菜 农家",
]


def search_douyin_web(keyword: str, count: int = 20) -> list[dict]:
    """
    通过抖音网页版搜索API获取视频标题

    注意：需要有效Cookie才能工作
    如果此方法失败，请使用手动采集方式
    """
    url = "https://www.douyin.com/aweme/v1/web/search/item/"
    params = {
        "keyword": keyword,
        "search_channel": "aweme_video_web",
        "sort_type": 0,  # 综合排序
        "publish_time": 0,
        "search_source": "normal_search",
        "count": count,
        "offset": 0,
    }

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()

        results = []
        for item in data.get("data", []):
            aweme = item.get("aweme_info", {})
            desc = aweme.get("desc", "")
            stats = aweme.get("statistics", {})

            if desc:
                results.append({
                    "title": desc,
                    "digg_count": stats.get("digg_count", 0),
                    "comment_count": stats.get("comment_count", 0),
                    "share_count": stats.get("share_count", 0),
                    "play_count": stats.get("play_count", 0),
                    "keyword": keyword,
                    "source": "抖音搜索",
                })

        return results

    except Exception as e:
        print(f"  抖音搜索失败（需要Cookie）: {keyword} - {e}")
        return []


def manual_titles():
    """
    手动采集槽位 — 需要你从抖音APP手动采集真实视频标题

    采集SOP：
      1. 打开抖音APP，搜索"脐橙""草莓""苹果"等品类关键词
      2. 切换到"视频"Tab，按"最多点赞"排序
      3. 复制播放量>10万的视频标题
      4. 按以下格式填入：
         {"title": "视频标题原文", "category": "品类", 
          "source": "抖音@账号名", "views_approx": 播放量万次}
      5. 运行脚本自动合并

    ⚠️ 此列表必须填入真实数据，禁止AI生成
    """
    return [
        # 在此粘贴你从抖音手动复制的真实视频标题
        # 示例格式（请替换为真实数据）：
        # {"title": "真实视频标题", "category": "脐橙",
        #  "source": "抖音@真实账号名", "views_approx": 50},
    ]


def main():
    print("=" * 60)
    print("抖音视频标题爬虫 — 采集三农爆款选题")
    print("=" * 60)

    all_titles = []

    # 方式1：API抓取（需Cookie）
    for kw in SEARCH_KEYWORDS:
        print(f"\n搜索: {kw}")
        results = search_douyin_web(kw)
        if results:
            all_titles.extend(results)
            print(f"  API获取: {len(results)}条")
        time.sleep(random.uniform(2.0, 4.0))

    # 方式2：手动采集的标题（保底数据）
    manual = manual_titles()
    all_titles.extend(manual)
    print(f"\n手动采集标题: {len(manual)}条")

    # 去重
    seen = set()
    unique = []
    for t in all_titles:
        if t["title"] not in seen:
            seen.add(t["title"])
            unique.append(t)

    # 保存
    output_file = os.path.join(OUTPUT_DIR, "dy_titles.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"采集完成！")
    print(f"  标题: {len(unique)}条（去重后）")
    print(f"  保存: {output_file}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

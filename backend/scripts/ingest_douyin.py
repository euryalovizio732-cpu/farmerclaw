"""
抖音采集数据 → 样本库入库工具

功能：
1. 读取 data/douyin_raw/*.json
2. 清洗标题（去抖音后缀、提取点赞数）
3. 自动分类 hook_type
4. 生成可直接粘贴到 sample_library.py 的代码片段
5. 也输出 JSON 便于程序化导入

用法:
  python scripts/ingest_douyin.py                     # 处理全部
  python scripts/ingest_douyin.py --file xxx.json     # 处理单个文件
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "douyin_raw"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

# ── 清洗规则 ──

# 去掉抖音后缀：「于20260409发布在抖音，已经收获了...来抖音，记录美好生活！」
DOUYIN_SUFFIX_RE = re.compile(
    r"\s*-?\s*\S{2,20}于\d{8}发布在抖音.*$", re.DOTALL
)

# 提取点赞数
LIKES_RE = re.compile(r"收获了([\d.]+)(万?)个喜欢")

# hook_type 自动分类关键词
HOOK_CLASSIFIERS = [
    ("价格冲击", ["元", "斤", "包邮", "便宜", "划算", "性价比", "价格", "秒杀", "特价"]),
    ("产地溯源", ["坐标", "自家", "果园", "产地", "直发", "原产", "正宗", "源头"]),
    ("季节稀缺", ["当季", "应季", "现摘", "限量", "抢", "最后", "错过", "新鲜上市"]),
    ("知识反问", ["为什么", "你知道", "怎么", "区别", "真假", "挑选", "辨别", "?", "？"]),
    ("情绪共鸣", ["妈妈", "家人", "小时候", "回忆", "故乡", "思念", "送礼", "孝"]),
    ("售后信任", ["包赔", "坏果", "售后", "不满意", "退款", "保障", "品质"]),
]

# 最小有效内容长度
MIN_CONTENT_LEN = 15

# 无效内容黑名单
BLACKLIST_PHRASES = ["搜索", "直播间", "点击进入", "复制链接"]


def extract_likes(title: str) -> int:
    """从标题中提取近似点赞数"""
    m = LIKES_RE.search(title)
    if not m:
        return 0
    num = float(m.group(1))
    if m.group(2) == "万":
        num *= 10000
    return int(num)


def clean_title(title: str) -> str:
    """清洗标题，去掉抖音后缀和多余 hashtag"""
    if not title:
        return ""
    # 去后缀
    cleaned = DOUYIN_SUFFIX_RE.sub("", title).strip()
    # 去末尾连续 hashtag（保留内容中的）
    cleaned = re.sub(r"(\s*#\S+)+\s*$", "", cleaned).strip()
    # 去多余换行
    cleaned = re.sub(r"\n{2,}", "\n", cleaned).strip()
    return cleaned


def extract_hashtags(title: str) -> list[str]:
    """提取所有 hashtag"""
    return re.findall(r"#(\S+?)(?:\s|$|#)", title)


def classify_hook(text: str) -> str:
    """基于关键词自动分类 hook_type"""
    scores = {}
    for hook_type, keywords in HOOK_CLASSIFIERS:
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[hook_type] = score
    if not scores:
        return "待分类"
    return max(scores, key=scores.get)


def is_usable(title: str, cleaned: str) -> bool:
    """判断是否为可用样本"""
    if len(cleaned) < MIN_CONTENT_LEN:
        return False
    if any(bp == cleaned for bp in BLACKLIST_PHRASES):
        return False
    return True


def process_file(json_path: Path) -> list[dict]:
    """处理单个 JSON 文件"""
    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    results = []
    for item in items:
        title = item.get("title", "")
        url = item.get("url", "")
        keyword = item.get("keyword", "")

        likes = extract_likes(title)
        cleaned = clean_title(title)
        hashtags = extract_hashtags(title)
        hook_type = classify_hook(cleaned)
        usable = is_usable(title, cleaned)

        results.append({
            "original_title": title,
            "cleaned_script": cleaned,
            "hook_type": hook_type,
            "hashtags": hashtags,
            "likes_approx": likes,
            "url": url,
            "keyword": keyword,
            "usable": usable,
            "verified_hit": likes >= 10000,
            "source_file": json_path.name,
        })

    return results


def to_sample_library_code(samples: list[dict], category: str) -> str:
    """生成可粘贴到 sample_library.py 的 Python 代码"""
    lines = [f"# ── 抖音真实样本 ({category}) ── 入库时间: {datetime.now().strftime('%Y-%m-%d')}"]
    for i, s in enumerate(samples, 1):
        if not s["usable"]:
            continue
        script = s["cleaned_script"].replace('"', '\\"')
        lines.append(f"""
# 样本 {i} — 点赞: {s['likes_approx']} | hook: {s['hook_type']}
{{
    "script": "{script}",
    "hook_type": "{s['hook_type']}",
    "source": "抖音采集 {s['url']}",
    "views_approx": {s['likes_approx'] * 20},  # 估算: 点赞×20≈播放
    "verified_hit": {s['verified_hit']},
    "usable_direct": True,
}},""")
    return "\n".join(lines)


def guess_category(keyword: str) -> str:
    """从搜索关键词猜品类"""
    cat_map = {
        "脐橙": "脐橙", "橙": "脐橙",
        "苹果": "苹果",
        "草莓": "草莓",
        "大米": "粮油", "五常": "粮油", "粮油": "粮油",
        "蔬菜": "蔬菜",
        "蓝莓": "蓝莓",
        "樱桃": "樱桃",
        "猕猴桃": "猕猴桃",
    }
    for k, v in cat_map.items():
        if k in keyword:
            return v
    return "其他"


def main():
    # 确定处理文件
    if "--file" in sys.argv:
        idx = sys.argv.index("--file") + 1
        files = [RAW_DIR / sys.argv[idx]]
    else:
        files = sorted(RAW_DIR.glob("*.json"))

    if not files:
        print("❌ 没有找到 JSON 文件，请检查 data/douyin_raw/ 目录")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_samples = []

    for f in files:
        print(f"\n{'='*60}")
        print(f"📂 处理: {f.name}")
        samples = process_file(f)
        category = guess_category(samples[0]["keyword"] if samples else "")
        all_samples.extend(samples)

        usable = [s for s in samples if s["usable"]]
        hits = [s for s in usable if s["verified_hit"]]

        print(f"   总计: {len(samples)} 条 | 可用: {len(usable)} 条 | 爆款(>1万赞): {len(hits)} 条")

        for s in samples:
            status = "✅" if s["usable"] else "❌"
            hit = "🔥" if s["verified_hit"] else "  "
            print(f"   {status}{hit} [{s['hook_type']:6s}] 赞:{s['likes_approx']:>7d} | {s['cleaned_script'][:50]}...")

        # 生成代码片段
        if usable:
            code = to_sample_library_code(samples, category)
            code_path = OUTPUT_DIR / f"{f.stem}_samples.py"
            code_path.write_text(code, encoding="utf-8")
            print(f"\n   📝 代码片段已生成: {code_path.relative_to(RAW_DIR.parent.parent)}")

    # 汇总
    print(f"\n{'='*60}")
    print(f"📊 汇总")
    total = len(all_samples)
    usable_total = sum(1 for s in all_samples if s["usable"])
    hits_total = sum(1 for s in all_samples if s["verified_hit"])
    print(f"   总采集: {total} | 可用: {usable_total} | 爆款: {hits_total}")
    print(f"   样本质量: {usable_total/total*100:.0f}%" if total > 0 else "")

    # 保存全量 JSON
    out_json = OUTPUT_DIR / f"all_processed_{datetime.now().strftime('%Y%m%d')}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_samples, f, ensure_ascii=False, indent=2)
    print(f"   💾 全量数据: {out_json.relative_to(RAW_DIR.parent.parent)}")


if __name__ == "__main__":
    main()

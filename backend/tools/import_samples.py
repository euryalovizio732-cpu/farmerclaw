"""
采集数据导入工具
================
将书签工具采集的 JSON 文件转换为 sample_library.py 可直接粘贴的代码片段。

用法:
  python -m tools.import_samples --file data/douyin_raw/xxx.json --category 脐橙
  python -m tools.import_samples --dir data/douyin_raw/ --category 草莓
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "samples_ready"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_json(file_path: str) -> list[dict]:
    """加载 JSON 采集文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "results" in data:
        return data["results"]
    return [data]


def classify_hook_type(text: str) -> str:
    """根据文案内容自动分类钩子类型"""
    text = text[:100].lower()

    # 价格冲击型
    price_kws = ["块钱", "元", "价格", "便宜", "划算", "福利", "亏本", "成本", "批发价", "出厂价", "9.9", "19.9"]
    if any(k in text for k in price_kws):
        return "价格冲击"

    # 知识反问型
    question_kws = ["你知道", "为什么", "怎么", "到底", "真的假的", "区别", "哪个", "？", "吗"]
    if any(k in text for k in question_kws):
        return "知识反问"

    # 产地溯源型
    origin_kws = ["产地", "果园", "基地", "山上", "地里", "树上", "现摘", "溯源", "原产地", "自家"]
    if any(k in text for k in origin_kws):
        return "产地溯源"

    # 季节稀缺型
    season_kws = ["应季", "当季", "最后", "再不买", "就没了", "错过", "限时", "赶紧", "仅剩", "霜降"]
    if any(k in text for k in season_kws):
        return "季节稀缺"

    # 情绪共鸣型
    emotion_kws = ["家人", "孩子", "妈妈", "爸爸", "老人", "小时候", "记忆", "回忆", "感动", "心疼"]
    if any(k in text for k in emotion_kws):
        return "情绪共鸣"

    return "待分类"


def process_samples(raw_list: list[dict], category: str) -> list[dict]:
    """处理原始采集数据为样本库格式"""
    samples = []
    seen = set()

    for item in raw_list:
        desc = item.get("desc", "").strip()
        if not desc or len(desc) < 10:
            continue
        # 去重
        key = desc[:50]
        if key in seen:
            continue
        seen.add(key)

        author = item.get("author", "未知")
        url = item.get("url", "")
        digg = item.get("digg", item.get("likes", 0))
        comment_count = item.get("comment", item.get("comments_count", 0))

        # 解析互动数据（可能是 "1.2万" 格式）
        views_approx = _parse_count(digg)

        sample = {
            "script": desc,
            "hook_type": classify_hook_type(desc),
            "source": f"抖音@{author} {url}",
            "views_approx": views_approx,
            "usable_direct": False,  # 默认需人工审核
        }
        samples.append(sample)

    return samples


def _parse_count(val) -> int:
    """解析 '1.2万' / '12.3k' / 1200 等格式"""
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip()
    if not s or s == "-":
        return 0
    try:
        if "万" in s:
            return int(float(s.replace("万", "")) * 10000)
        elif "k" in s.lower():
            return int(float(s.lower().replace("k", "")) * 1000)
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def generate_code_snippet(samples: list[dict], category: str) -> str:
    """生成可直接粘贴到 sample_library.py 的代码"""
    lines = [
        f"# ═══ {category} 样本数据 ═══",
        f"# 来源：抖音采集 | 数量：{len(samples)} 条",
        f"# 生成时间：{datetime.now().isoformat()}",
        f"# 用法：复制下面的列表项到 sample_library.py → SAMPLES[\"{category}\"][\"script\"] 中",
        "",
    ]

    for i, s in enumerate(samples):
        script = s["script"].replace('"', '\\"').replace("\n", "\\n")
        lines.append(f"# ── 样本 {i+1} ({s['hook_type']}) ──")
        lines.append("{")
        lines.append(f'    "script": "{script}",')
        lines.append(f'    "hook_type": "{s["hook_type"]}",')
        lines.append(f'    "source": "{s["source"]}",')
        lines.append(f'    "views_approx": {s["views_approx"]},')
        lines.append(f'    "usable_direct": False,  # 人工审核后改为 True')
        lines.append("},")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="采集数据导入到样本库")
    parser.add_argument("--file", "-f", help="单个JSON文件路径")
    parser.add_argument("--dir", "-d", help="JSON文件目录（批量导入）")
    parser.add_argument("--category", "-c", required=True, help="品类名（如'脐橙'/'草莓'）")

    args = parser.parse_args()

    # 收集所有JSON文件
    files = []
    if args.file:
        files.append(Path(args.file))
    elif args.dir:
        files = sorted(Path(args.dir).glob("*.json"))
    else:
        print("❌ 请指定 --file 或 --dir")
        sys.exit(1)

    if not files:
        print("❌ 未找到任何JSON文件")
        sys.exit(1)

    # 加载所有数据
    all_raw = []
    for f in files:
        print(f"📂 加载: {f}")
        try:
            items = load_json(str(f))
            all_raw.extend(items)
            print(f"   → {len(items)} 条记录")
        except Exception as e:
            print(f"   ⚠️ 加载失败: {e}")

    if not all_raw:
        print("❌ 没有有效数据")
        sys.exit(1)

    # 处理为样本格式
    samples = process_samples(all_raw, args.category)
    print(f"\n✅ 有效样本: {len(samples)} 条（去重后）")

    # 钩子类型统计
    hook_stats: dict[str, int] = {}
    for s in samples:
        hook_stats[s["hook_type"]] = hook_stats.get(s["hook_type"], 0) + 1
    print("\n📊 钩子类型分布:")
    for ht, cnt in sorted(hook_stats.items(), key=lambda x: -x[1]):
        print(f"   {ht}: {cnt} 条")

    # 生成代码片段
    code = generate_code_snippet(samples, args.category)
    out_file = OUTPUT_DIR / f"{args.category}_samples.py"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"\n💾 代码片段已保存: {out_file}")
    print(f"   → 复制内容到 sample_library.py 的 SAMPLES[\"{args.category}\"][\"script\"] 列表中")
    print(f"   → 重启后端即生效（Few-shot自动启用）")

    # 同时保存处理后的JSON
    json_out = OUTPUT_DIR / f"{args.category}_samples.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON已保存: {json_out}")


if __name__ == "__main__":
    main()

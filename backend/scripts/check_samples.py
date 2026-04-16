import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.sample_library import SAMPLES, get_sample_stats


def report_target(title, targets, totals):
    print(f"\n{title}:  口播≥{targets['script']}  选题≥{targets['topic']}  直播≥{targets['live_module']}  痛点≥{targets['pain_point']}  回复≥{targets['reply']}")
    gaps = {k: max(0, targets[k] - totals[k]) for k in targets}
    print(f"缺口:  口播-{gaps['script']}  选题-{gaps['topic']}  直播-{gaps['live_module']}  痛点-{gaps['pain_point']}  回复-{gaps['reply']}")
    passed = sum(1 for k in targets if totals[k] >= targets[k])
    print(f"达标: {passed}/5  {'✅ 全部达标！' if passed == 5 else '❌ 继续补充'}")


s = get_sample_stats()
print("=== 样本库状态 ===")
print("总样本:", s["total_samples"])
print()
core_cats = ["脐橙", "苹果", "草莓", "粮油", "蔬菜", "蓝莓", "樱桃", "猕猴桃"]
cats = core_cats + ["通用"]
print(f"{'品类':<6} {'口播':>5} {'选题':>5} {'直播':>5} {'痛点':>5} {'回复':>5}")
print("-" * 35)
totals = {"script": 0, "topic": 0, "live_module": 0, "pain_point": 0, "reply": 0}
cat_stats = {}
for cat in cats:
    d = SAMPLES.get(cat, {})
    sc = len(d.get("script", []))
    tp = len(d.get("topic", []))
    lv = len(d.get("live_module", []))
    pp = len(d.get("pain_point", []))
    rp = len(d.get("reply", []))
    print(f"{cat:<6} {sc:5d} {tp:5d} {lv:5d} {pp:5d} {rp:5d}")
    cat_stats[cat] = {"script": sc, "topic": tp, "live_module": lv, "pain_point": pp, "reply": rp}
    totals["script"] += sc
    totals["topic"] += tp
    totals["live_module"] += lv
    totals["pain_point"] += pp
    totals["reply"] += rp

print("-" * 35)
print(f"{'合计':<6} {totals['script']:5d} {totals['topic']:5d} {totals['live_module']:5d} {totals['pain_point']:5d} {totals['reply']:5d}")
print()
base_targets = {"script": 120, "topic": 50, "live_module": 30, "pain_point": 50, "reply": 30}
stage2_targets = {"script": 120, "topic": 50, "live_module": 60, "pain_point": 50, "reply": 60}
core_targets = {"script": 13, "topic": 11, "live_module": 7, "pain_point": 7, "reply": 7}

report_target("基础目标", base_targets, totals)
report_target("商用一期目标", stage2_targets, totals)

print("\n=== 逐品类更厚更稳（核心8品类） ===")
print(f"目标: 口播≥{core_targets['script']}  选题≥{core_targets['topic']}  直播≥{core_targets['live_module']}  痛点≥{core_targets['pain_point']}  回复≥{core_targets['reply']}")
print(f"{'品类':<6} {'口播':>5} {'选题':>5} {'直播':>5} {'痛点':>5} {'回复':>5} {'状态':>6}")
print("-" * 44)

coverage_passed = 0
for cat in core_cats:
    counts = cat_stats[cat]
    ok = all(counts[k] >= core_targets[k] for k in core_targets)
    if ok:
        coverage_passed += 1
    print(f"{cat:<6} {counts['script']:5d} {counts['topic']:5d} {counts['live_module']:5d} {counts['pain_point']:5d} {counts['reply']:5d} {('✅' if ok else '❌'):>6}")
    if not ok:
        gaps = []
        if counts["script"] < core_targets["script"]:
            gaps.append(f"口播-{core_targets['script'] - counts['script']}")
        if counts["topic"] < core_targets["topic"]:
            gaps.append(f"选题-{core_targets['topic'] - counts['topic']}")
        if counts["live_module"] < core_targets["live_module"]:
            gaps.append(f"直播-{core_targets['live_module'] - counts['live_module']}")
        if counts["pain_point"] < core_targets["pain_point"]:
            gaps.append(f"痛点-{core_targets['pain_point'] - counts['pain_point']}")
        if counts["reply"] < core_targets["reply"]:
            gaps.append(f"回复-{core_targets['reply'] - counts['reply']}")
        print(f"{'':<6} 缺口: {' '.join(gaps)}")

print("-" * 44)
print(f"逐品类达标: {coverage_passed}/{len(core_cats)}  {'✅ 全部达标' if coverage_passed == len(core_cats) else '❌ 继续补齐'}")

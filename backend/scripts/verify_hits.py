"""Quick check: how many verified_hit samples per category, and does get_few_shot_samples prioritize them?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.sample_library import get_few_shot_samples, SAMPLES

cats = ["脐橙", "草莓", "粮油", "苹果", "蓝莓", "猕猴桃", "蔬菜", "樱桃"]
print("=== verified_hit 统计 ===")
for c in cats:
    for t in ["script", "topic"]:
        pool = SAMPLES.get(c, {}).get(t, [])
        v = sum(1 for s in pool if s.get("verified_hit"))
        print(f"  {c}/{t}: {v}/{len(pool)} verified")

print("\n=== get_few_shot_samples 优先级测试 ===")
for c in cats:
    samples = get_few_shot_samples(c, "script", 3)
    v = sum(1 for s in samples if s.get("verified_hit"))
    print(f"  {c}: 抽3条, verified={v}, sources={[s.get('source','')[:30] for s in samples]}")

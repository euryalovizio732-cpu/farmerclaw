import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
exec(open(os.path.join(os.path.dirname(__file__), '..', 'app', 'services', 'sample_library.py'), encoding='utf-8').read())

total = 0
verified = 0
print(f"{'品类':10s} | {'script':>6s} | {'topic':>5s} | {'live':>4s} | {'pain':>4s} | {'reply':>5s} | {'小计':>4s} | {'verified':>8s}")
print("-" * 75)
for k, v in SAMPLES.items():
    s = len(v.get('script', []))
    t = len(v.get('topic', []))
    l = len(v.get('live_module', []))
    p = len(v.get('pain_point', []))
    r = len(v.get('reply', []))
    sub = s + t + l + p + r
    vh = sum(1 for x in v.get('script', []) if x.get('verified_hit'))
    vh += sum(1 for x in v.get('topic', []) if x.get('verified_hit'))
    vh += sum(1 for x in v.get('live_module', []) if x.get('verified_hit'))
    vh += sum(1 for x in v.get('pain_point', []) if x.get('verified_hit'))
    vh += sum(1 for x in v.get('reply', []) if x.get('verified_hit'))
    total += sub
    verified += vh
    print(f"{k:10s} | {s:6d} | {t:5d} | {l:4d} | {p:4d} | {r:5d} | {sub:4d} | {vh:8d}")

print("-" * 75)
print(f"{'总计':10s} | {'':6s} | {'':5s} | {'':4s} | {'':4s} | {'':5s} | {total:4d} | {verified:8d}")
print(f"\n总样本数: {total}")
print(f"verified_hit 样本数: {verified}")

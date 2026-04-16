"""端到端测试：用大连大樱桃跑一次完整内容包，打印实际输出质量"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.content_pack_agent import content_pack_agent, ContentPackRequest

req = ContentPackRequest(
    product_name="大连大樱桃",
    category="樱桃",
    origin="大连旅顺",
    specification="2斤装",
    price="69.9元",
    core_features="美早品种，糖度17度，当天采摘当天发，顺丰冷链48小时达",
)

print("=" * 60)
print("正在生成内容包（需调用LLM，约30-60秒）...")
print("=" * 60)

result = content_pack_agent.generate(req)

print(f"\n日期: {result.date}")
print(f"完成阶段: {result.stages_completed}")
print(f"失败阶段: {result.stages_failed}")

print("\n" + "=" * 60)
print("【节气提示】")
print("=" * 60)
print(f"  节气: {result.season_info}")
print(f"  今日建议: {result.today_tip}")

print("\n" + "=" * 60)
print("【选题 × {}条】".format(len(result.topics)))
print("=" * 60)
for i, t in enumerate(result.topics, 1):
    print(f"\n  选题{i}: {t.get('title', '?')}")
    print(f"    类型: {t.get('type', '?')}")
    print(f"    核心冲突: {t.get('core_conflict', '?')}")
    print(f"    拍摄建议: {t.get('shooting_angle', '?')}")

print("\n" + "=" * 60)
print("【口播稿 × {}条】".format(len(result.scripts)))
print("=" * 60)
for i, s in enumerate(result.scripts, 1):
    print(f"\n  --- 口播稿{i} ({s.get('formula_type', '?')}型) ---")
    print(f"  对应选题: {s.get('topic_title', '?')}")
    script_text = s.get('full_script', '')
    print(f"  全文({len(script_text)}字):")
    print(f"  {script_text}")
    print(f"  钩子: {s.get('hook_0_3s', '')[:60]}...")

print("\n" + "=" * 60)
print("【直播话术积木块】")
print("=" * 60)
for module_type, modules in result.live_modules.items():
    print(f"\n  [{module_type}] ({len(modules)}条)")
    for m in modules[:2]:
        print(f"    - {m.get('name', '?')}: {m.get('script', '')[:80]}...")

print("\n" + "=" * 60)
print("【标签】")
print("=" * 60)
print(f"  {result.hashtags}")

print("\n" + "=" * 60)
print("【合规检查】")
print("=" * 60)
print(f"  {result.compliance}")

print("\n" + "=" * 60)
print("完成！")

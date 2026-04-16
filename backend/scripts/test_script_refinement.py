"""
实测 ScriptAgent 的“生成-评审-重写”链路
"""
import sys
import os
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.script_agent import script_agent
from app.services.golden_scripts import REFERENCE_POOL

def test_script_generation():
    # 1. 模拟一个内容包请求
    test_cases = [
        {
            "product": "美早大樱桃",
            "category": "大连大樱桃",
            "topic": {
                "title": "大连美早，产地直发",
                "core_conflict": "商超美早贵且不新鲜",
                "shooting_angle": "直接在果树下采摘，展示果柄绿色和脆度"
            },
            "context": {
                "origin": "大连东港",
                "specification": "单果26mm+ (JJ级)",
                "price": "98元/3斤",
                "core_features": "顺丰空运，坏果包赔"
            }
        },
        {
            "product": "丹东红颜草莓",
            "category": "丹东草莓",
            "topic": {
                "title": "自然熟的草莓才够甜",
                "core_conflict": "催熟草莓发酸，且中间是白的",
                "shooting_angle": "掰开草莓，展示红润的果肉和浓郁奶香味"
            },
            "context": {
                "origin": "辽宁丹东东港",
                "specification": "一盒30颗 约1.5kg",
                "price": "148元",
                "core_features": "自然熟，九分熟采摘，坏果包赔"
            }
        }
    ]

    for i, case in enumerate(test_cases):
        logger.info(f"--- 测试用例 {i+1}: {case['product']} ---")
        
        result = script_agent.generate_with_review(
            product_name=case['product'],
            category=case['category'],
            topic_info=case['topic'],
            context=case['context']
        )
        
        print("\n[Stage 1: Draft 初稿]")
        print(result['draft'])
        
        print(f"\n[Stage 2: Review 评审] 分数: {result['review'].get('score')}")
        print(f"问题: {result['review'].get('issues')}")
        print(f"建议: {result['review'].get('suggestions')}")
        
        print("\n[Stage 3: Final 最终交付稿]")
        print(result['full_script'])
        print("-" * 50)

if __name__ == "__main__":
    test_script_generation()

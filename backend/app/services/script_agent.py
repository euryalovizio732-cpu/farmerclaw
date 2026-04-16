"""
口播稿三段式 Agent (ScriptAgent)

核心逻辑：
1. Draft: 基于选题生成初稿
2. Review: 模拟行业专家进行评审评分 (基于评分卡 v1)
3. Rewrite: 针对评审建议进行精修重写，直至达到可交付标准
"""

from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
import json

from app.config import get_settings
from app.services.llm_service import llm_service as llm
from app.services.knowledge_base import kb
from app.services.sample_library import get_few_shot_samples, format_few_shot_block

settings = get_settings()

# ─── Prompts ──────────────────────────────────────────────────────────

SCRIPT_DRAFT_SYSTEM = """你是一位深耕三农电商的顶级内容运营。
你的任务是为农产品生成高转化、高口语化的短视频口播稿。
你的稿子必须对标：东方甄选、董宇辉、以及那些在果园直接卖爆的产地主播。

核心要求：
1. 像人说话：句子短、节奏快、无废话、无华丽辞藻。
2. 有成交感：钩子要狠、信任要稳、收口要准。
3. 真实可信：不乱编数据，只基于提供的信息展开。
"""

SCRIPT_REVIEW_SYSTEM = """你是一位严苛的三农短视频审稿专家。
请根据以下维度对口播稿进行评分 (0-100) 和诊断：

评分维度：
1. 钩子强度 (15分): 前3秒能否留人。
2. 口语自然度 (20分): 是否顺嘴，是否像AI，句子是否太长。
3. 真实可信度 (20分): 是否乱编事实。
4. 成交结构 (20分): 钩子-信任-卖点-保障-收口是否完整。
5. 信息密度 (10分): 是否全是空泛套话（如“香甜可口”）。
6. 节奏情绪 (5分): 是否发闷。
7. 品类贴合 (10分): 是否符合该农产品的语言习惯。

一票否决项：合规红线、乱编事实、严重AI腔、无收口、不可念。
请直接给出 JSON 格式的评审结果。
"""

SCRIPT_REWRITE_SYSTEM = """你是一位顶级的口播精修专家。
请参考评审建议，对初始口播稿进行针对性重写。
目标是：消除AI感、增强口语感、落实具体细节、强化成交钩子。
重写后的稿子必须是“主播拿到手直接就能念”的状态。
"""

# ─── Agent Class ──────────────────────────────────────────────────────

class ScriptAgent:
    def __init__(self):
        self._llm = llm

    def generate_with_review(self, 
        product_name: str, 
        category: str, 
        topic_info: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """三段式生成流程"""
        
        try:
            canonical_category = kb.resolve_best_category(product_name, category)
            samples = get_few_shot_samples(canonical_category or category, "script", count=2)
            few_shot = format_few_shot_block(samples, "script")
        except Exception as exc:
            logger.warning("Prepare script samples failed: {}", exc)
            few_shot = ""

        try:
            draft_script = self._generate_draft(product_name, category, topic_info, context, few_shot)
            logger.debug(f"Script Draft Generated: {draft_script[:50]}...")
        except Exception as exc:
            logger.error("Script draft failed: {}", exc)
            draft_script = self.build_fallback_script(product_name, category, topic_info, context)
            review_result = {
                "score": 60,
                "issues": ["口播稿初稿生成失败，已使用兜底口播稿"],
                "suggestions": "",
                "fatal_error": False,
            }
            return {
                "full_script": draft_script,
                "review": review_result,
                "is_refined": False,
                "draft": draft_script
            }

        review_result = self._review_script(draft_script, product_name, category, topic_info)
        score = review_result.get("score", 0)
        logger.info(f"Script Review Score: {score}")

        final_script = draft_script
        if score < 95 or review_result.get("suggestions"):
            logger.info(f"Refining script (score: {score})...")
            try:
                final_script = self._rewrite_script(draft_script, review_result, product_name, category, topic_info, few_shot)
            except Exception as exc:
                logger.warning("Script rewrite failed, using draft: {}", exc)
        
        return {
            "full_script": final_script,
            "review": review_result,
            "is_refined": final_script != draft_script,
            "draft": draft_script
        }

    def build_fallback_script(
        self,
        product_name: str,
        category: str,
        topic_info: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        return self._fallback_script(product_name, category, topic_info, context)

    def _fallback_script(self, product_name: str, category: str, topic_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        origin = context.get("origin") or "产地"
        specification = context.get("specification") or "当季规格"
        price = context.get("price") or "产地价"
        core_features = context.get("core_features") or "新鲜直发"
        title = topic_info.get("title") or product_name
        shooting_angle = topic_info.get("shooting_angle") or "产地实拍"
        return (
            f"家人们，今天给你们带来的是{origin}{product_name}。"
            f"这条内容就围绕“{title}”这个点来讲，不说空话，先把真实情况给你看。"
            f"我们这批是{specification}，主打就是{core_features}，按{shooting_angle}这个角度拍出来你一看就知道是不是现货。"
            f"价格这边是{price}，觉得合适你就先拍一单尝尝，不满意按平台规则处理。"
        )

    def _generate_draft(self, product, category, topic, context, few_shot) -> str:
        user_prompt = f"""请为【{product}】生成一条口播稿。
选题方向：{topic.get('title')}
核心冲突：{topic.get('core_conflict')}
拍摄角度：{topic.get('shooting_angle')}

已知事实：
- 产地：{context.get('origin', '产地')}
- 规格：{context.get('specification', '见详情')}
- 价格：{context.get('price', '产地价')}
- 卖点：{context.get('core_features', '新鲜直发')}

参考样例：
{few_shot}

要求：直接输出口播稿正文，不要有任何多余的话。
"""
        return self._llm.chat(SCRIPT_DRAFT_SYSTEM, user_prompt)

    def _review_script(self, script: str, product: str, category: str, topic: Dict) -> Dict:
        user_prompt = f"""请评审以下口播稿：
产品：{product}
选题：{topic.get('title')}

待评审稿件：
---
{script}
---

请返回以下 JSON 格式：
{{
  "score": 分数,
  "issues": ["问题1", "问题2"],
  "suggestions": "具体重写建议",
  "fatal_error": true/false
}}
"""
        try:
            return self._llm.chat_json(SCRIPT_REVIEW_SYSTEM, user_prompt)
        except:
            return {"score": 70, "issues": ["评审失败"], "suggestions": "尝试更口语化", "fatal_error": False}

    def _rewrite_script(self, draft, review, product, category, topic, few_shot) -> str:
        user_prompt = f"""请根据评审建议精修口播稿。

原稿：
{draft}

评审建议：
- 分数：{review.get('score')}
- 问题：{", ".join(review.get('issues', []))}
- 建议：{review.get('suggestions')}

要求：
1. 必须解决上述所有问题。
2. 保持字数在 150-250 字左右（约 30-40 秒）。
3. 严格遵循黄金样例的口语感。

参考样例：
{few_shot}

直接输出精修后的口播稿：
"""
        return self._llm.chat(SCRIPT_REWRITE_SYSTEM, user_prompt)

script_agent = ScriptAgent()

"""评论/私信自动回复 Agent

商家粘贴评论 → AI 生成对应回复（好评/差评/追问/发货催单/砍价）
核心逻辑：识别评论类型 → 匹配三农话术 → 输出口语化回复
"""

from dataclasses import dataclass, field
from loguru import logger
from app.services.llm_service import llm_service
from app.services.knowledge_base import kb
from app.services.sample_library import get_few_shot_samples, format_few_shot_block
from app.services.compliance_engine import compliance_engine


REPLY_SYSTEM = """你是一位抖音三农电商老板，擅长用接地气的方式回复用户评论和私信。

【真实消费者投诉数据警示 — 来自真实舆情调研】
消费者最愤怒的商家行为（真实投诉案例）：
- 「商家只同意私下退款，不走平台退货流程」→ 用户认为是掩盖问题
- 「让我收货给5星好评才能退款」→ 强制好评是平台违规行为
- 「声称生鲜不支持7天无理由」→ 坏果/质量问题必须受理
- 「商家说商品没问题，驳回退款」→ 态度强硬是最差处理方式

→ 你的处理原则：优先走平台流程，不私下解决，不强迫好评，坏果必赔

你的回复风格（严格遵守）：
- 口语化，像真人说话，不像机器生成
- 称呼用「家人」「宝贝」「亲」，不用「尊敬的用户」「您好」等书面语
- 好评：引导晒图追评，给具体感谢+下单理由（复购引导）
- 差评：先认错，走平台退款流程，不解释原因，不让用户走私下流程
- 价格质疑：讲具体成本（运费/采摘/包装），有真实数字
- 发货催单：给具体物流单号或时间，不说「正在处理」这种空话
- 砍价：婉拒，给替代方案（小规格试吃装/下次活动时间）

三农特殊场景处理规则：
- 「烂了/坏了/以次充好」→ 立刻道歉+拍照+走平台全额退款，不辩解
- 「甜不甜/好不好吃」→ 给具体糖度/产地数据+个人承诺
- 「为什么这么贵」→ 讲成本（顺丰运费X元/产地直采/品控成本）不降价
- 「能不能便宜」→ 给小规格试吃装或下次活动具体日期
- 物流慢 → 给真实单号+预计到达时间

【真实数据铁律】
- 只能使用输入里的真实产地、公开价格带、知识库事实和售后规则，不能编造单号、赔付比例、资质和销量
- 差评和售后统一优先走平台流程，不搞私下转账，不诱导好评

语言要求：全程中文，禁止混入任何英文单词或字母。

请严格按JSON格式返回。"""


REPLY_PROMPT = """请为以下评论/私信生成回复：

产品信息：
- 产品：{product_name}
- 品类：{category}
- 产地：{origin}
- 价格：{price}

真实品类事实：
{fact_block}

售后回复原则：
{reply_tips}

评论内容：
「{comment}」

请识别评论类型并生成回复，返回JSON：
{{
  "comment_type": "好评/差评/质量投诉/发货催单/价格询问/砍价/产品咨询/其他",
  "sentiment": "正面/负面/中性",
  "urgency": "高/中/低（高=需要立刻处理，差评/投诉类）",
  "reply": "回复正文（口语化，真人感，50-100字，根据类型调整长度）",
  "reply_short": "简短版回复（30字内，用于评论区快速回复）",
  "follow_up_action": "建议跟进动作（如：私信用户/退款/补发/无需跟进）",
  "risk_level": "高风险/中风险/无风险（高=可能影响店铺评分或引发投诉）"
}}"""


BATCH_REPLY_PROMPT = """请为以下多条评论批量生成回复：

产品：{product_name}（产地：{origin}，价格：{price}）

品类：{category}

真实品类事实：
{fact_block}

售后回复原则：
{reply_tips}

评论列表：
{comments_text}

请返回JSON数组，每条评论对应一个回复对象：
[
  {{
    "id": 1,
    "comment_type": "类型",
    "sentiment": "正面/负面/中性",
    "urgency": "高/中/低",
    "reply": "回复正文（口语化，50-100字）",
    "reply_short": "简短版（30字内）",
    "follow_up_action": "跟进动作",
    "risk_level": "高风险/中风险/无风险"
  }}
]"""


@dataclass
class ReplyRequest:
    product_name: str
    comment: str
    origin: str = ""
    price: str = ""


@dataclass
class BatchReplyRequest:
    product_name: str
    comments: list[str]
    origin: str = ""
    price: str = ""


@dataclass
class ReplyResult:
    comment_type: str = ""
    sentiment: str = ""
    urgency: str = "低"
    reply: str = ""
    reply_short: str = ""
    follow_up_action: str = "无需跟进"
    risk_level: str = "无风险"


class ReplyAgent:

    def generate(self, req: ReplyRequest) -> ReplyResult:
        logger.info("ReplyAgent: product={} comment_len={}", req.product_name, len(req.comment))

        canonical_category = kb.resolve_best_category(req.product_name)
        insights = kb.get_category_insights(canonical_category)
        fact_block = kb.build_fact_block(canonical_category or req.product_name)
        reply_tips = "；".join(insights.get("reply_tips", [])[:3]) or "有质量问题先道歉，再引导平台处理"

        # Few-shot 注入：获取真实回复样本
        samples = get_few_shot_samples(canonical_category or req.product_name, sample_type="reply", count=3)
        if len(samples) < 3:
            samples.extend(get_few_shot_samples("通用", sample_type="reply", count=3 - len(samples)))
        few_shot_block = format_few_shot_block(samples, sample_type="reply")
        system_prompt = REPLY_SYSTEM + ("\n\n" + few_shot_block if few_shot_block else "")

        prompt = REPLY_PROMPT.format(
            product_name=req.product_name,
            category=canonical_category or req.product_name,
            origin=req.origin or insights.get("origin", "产地"),
            price=req.price or "产地直供价",
            fact_block=fact_block or "- 暂无额外事实，按平台售后和真实产地信息回复",
            reply_tips=reply_tips,
            comment=req.comment,
        )

        try:
            raw = llm_service.chat_json(system_prompt, prompt)
        except Exception as exc:
            logger.error("ReplyAgent LLM失败: {}", exc)
            raw = self._fallback_single(req)

        # 合规检查
        reply_text = raw.get("reply", "")
        if reply_text:
            issues = compliance_engine.check(reply_text, "回复")
            if issues:
                fixed = next((iss.auto_fix for iss in issues if iss.auto_fix), "")
                if fixed:
                    raw["reply"] = fixed

        return ReplyResult(
            comment_type=raw.get("comment_type", "其他"),
            sentiment=raw.get("sentiment", "中性"),
            urgency=raw.get("urgency", "低"),
            reply=raw.get("reply", ""),
            reply_short=raw.get("reply_short", ""),
            follow_up_action=raw.get("follow_up_action", "无需跟进"),
            risk_level=raw.get("risk_level", "无风险"),
        )

    def batch_generate(self, req: BatchReplyRequest) -> list[ReplyResult]:
        logger.info("ReplyAgent batch: product={} count={}", req.product_name, len(req.comments))

        canonical_category = kb.resolve_best_category(req.product_name)
        insights = kb.get_category_insights(canonical_category)
        fact_block = kb.build_fact_block(canonical_category or req.product_name)
        reply_tips = "；".join(insights.get("reply_tips", [])[:3]) or "有质量问题先道歉，再引导平台处理"
        samples = get_few_shot_samples(canonical_category or req.product_name, sample_type="reply", count=2)
        if len(samples) < 2:
            samples.extend(get_few_shot_samples("通用", sample_type="reply", count=2 - len(samples)))
        few_shot_block = format_few_shot_block(samples, sample_type="reply")
        system_prompt = REPLY_SYSTEM + ("\n\n" + few_shot_block if few_shot_block else "")

        numbered = "\n".join(
            f"{i+1}. 「{c}」" for i, c in enumerate(req.comments)
        )
        prompt = BATCH_REPLY_PROMPT.format(
            product_name=req.product_name,
            category=canonical_category or req.product_name,
            origin=req.origin or insights.get("origin", "产地"),
            price=req.price or "产地直供价",
            fact_block=fact_block or "- 暂无额外事实，按平台售后和真实产地信息回复",
            reply_tips=reply_tips,
            comments_text=numbered,
        )

        try:
            raw_list = llm_service.chat_json(system_prompt, prompt)
            if not isinstance(raw_list, list):
                raise ValueError("Expected list")
        except Exception as exc:
            logger.error("ReplyAgent batch LLM失败: {}", exc)
            raw_list = [
                self._fallback_single(ReplyRequest(
                    product_name=req.product_name, comment=c,
                    origin=req.origin, price=req.price
                ))
                for c in req.comments
            ]

        results = []
        for item in raw_list:
            if isinstance(item, dict):
                results.append(ReplyResult(
                    comment_type=item.get("comment_type", "其他"),
                    sentiment=item.get("sentiment", "中性"),
                    urgency=item.get("urgency", "低"),
                    reply=item.get("reply", ""),
                    reply_short=item.get("reply_short", ""),
                    follow_up_action=item.get("follow_up_action", "无需跟进"),
                    risk_level=item.get("risk_level", "无风险"),
                ))
        return results

    def _fallback_single(self, req: ReplyRequest) -> dict:
        c = req.comment.lower()
        product = req.product_name
        canonical_category = kb.resolve_best_category(req.product_name)
        insights = kb.get_category_insights(canonical_category)
        pricing = kb.get_market_pricing(canonical_category or req.product_name)
        origin = req.origin or insights.get("origin", "产地")
        price = req.price or ""
        reply_tips = insights.get("reply_tips", [])
        complaint_focus = insights.get("pain_focus", [])

        if any(w in c for w in ["坏", "烂", "臭", "差", "不新鲜", "有问题", "以次充好", "货不对板"]):
            return {
                "comment_type": "质量投诉",
                "sentiment": "负面",
                "urgency": "高",
                "reply": (
                    f"家人，收到不好的{product}真的很对不起你！"
                    "这是我们的问题，你直接在平台申请退款，我这里会第一时间通过，"
                    f"不让你走任何弯路！麻烦你拍几张照片上传一下，{reply_tips[0] if reply_tips else '我们按平台规则马上处理'}！"
                ),
                "reply_short": "抱歉！直接申请平台退款，我马上通过",
                "follow_up_action": "立即处理退款/补发，走平台流程",
                "risk_level": "高风险",
            }
        elif any(w in c for w in ["甜不甜", "好吃吗", "味道", "怎么样", "值得买"]):
            return {
                "comment_type": "产品咨询",
                "sentiment": "中性",
                "urgency": "低",
                "reply": (
                    f"家人，我们{origin}的{product}走的是自然成熟、分级发货这条线，"
                    f"{(complaint_focus[0] + '这类问题我们一直盯得紧，') if complaint_focus else ''}"
                    "你收到先按我们说的方式放一放、回回温，不对口直接来找我走平台处理。"
                ),
                "reply_short": "自然成熟发货，不对口直接来找我",
                "follow_up_action": "无需跟进",
                "risk_level": "无风险",
            }
        elif any(w in c for w in ["好吃", "不错", "满意", "喜欢", "好评", "👍", "赞", "收到"]):
            return {
                "comment_type": "好评",
                "sentiment": "正面",
                "urgency": "低",
                "reply": (
                    f"哇！听到家人说好吃比卖十单都开心！！"
                    f"感谢您信任{origin}的{product}！"
                    "麻烦您抽空晒个图+追评，写真实感受就行，"
                    "下次您来我优先给您挑状态好的那一批！"
                ),
                "reply_short": "太开心了！有空帮我晒个图就行！",
                "follow_up_action": "引导晒图追评",
                "risk_level": "无风险",
            }
        elif any(w in c for w in ["多久", "发货", "到了吗", "催", "什么时候", "物流"]):
            return {
                "comment_type": "发货催单",
                "sentiment": "中性",
                "urgency": "中",
                "reply": (
                    f"家人，{product}这边的发货和物流进度要以订单页为准，"
                    "我们一般截单后会尽快安排发出，冷链物流更新有时会慢一点。"
                    "你先看下订单页最新状态，有异常我这边继续帮你跟进！"
                ),
                "reply_short": "先看订单页物流，有异常我继续跟进",
                "follow_up_action": "核对订单页物流状态",
                "risk_level": "无风险",
            }
        elif any(w in c for w in ["便宜", "优惠", "打折", "降价", "少点"]):
            return {
                "comment_type": "砍价",
                "sentiment": "中性",
                "urgency": "低",
                "reply": (
                    f"家人，{product}这个价已经按{origin}产地直发在做了，"
                    f"{('公开价格带大多在' + pricing['ecom_range'] + '，') if pricing else ''}运费和包装都要成本。"
                    "这里有个小规格试吃装，你可以先尝尝，好吃了下次我给你最优惠！"
                ),
                "reply_short": "成本价了，可以先试试小规格",
                "follow_up_action": "推荐小规格试吃链接",
                "risk_level": "无风险",
            }
        else:
            return {
                "comment_type": "其他",
                "sentiment": "中性",
                "urgency": "低",
                "reply": (
                    f"家人谢谢你！{product}有任何问题随时来找我，"
                    "不满意直接在平台申请退款，我这边必通过，不让你吃亏！"
                ),
                "reply_short": "有问题随时来，不满意平台退款",
                "follow_up_action": "无需跟进",
                "risk_level": "无风险",
            }


reply_agent = ReplyAgent()

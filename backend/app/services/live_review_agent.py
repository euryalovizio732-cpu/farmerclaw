"""直播复盘 Agent

商家直播结束后输入数据 → AI 自动生成：
  - 本场问题诊断（哪个环节掉人/低转化）
  - 话术改进建议（口语化，直接可用）
  - 下场直播行动计划（排品/节奏/话术）
  - 竞品对比视角
"""

from dataclasses import dataclass, field
from loguru import logger
from app.services.llm_service import llm_service
from app.services.sample_library import get_few_shot_samples, format_few_shot_block


LIVE_REVIEW_SYSTEM = """你是一位抖音三农直播运营专家，服务过百场以上三农品类直播。

你擅长：
- 通过数据发现直播问题（掉人节点/低转化环节）
- 用口语化方式给出可落地的改进建议
- 三农品类的特殊规律（时令/产地/信任建立）

分析框架：
1. 流量漏斗分析（进场→停留→互动→下单）
2. 话术节奏问题（引流款→爆款→利润款）
3. 选品结构问题（SKU数量/价格带/爆款占比）
4. 信任建立节点（产地展示/资质/实拍）

输出要求：
- 问题诊断要直接，不说废话，说清楚「哪里掉了/为什么」
- 改进建议要口语化，可以直接执行，不是大道理
- 每条建议要量化：「把开场话术改成30秒内」而不是「缩短开场话术」
- 对三农品类要有行业认知：水果类最怕运费疑虑/蔬菜类最怕新鲜度疑虑

请严格按JSON格式返回。"""


LIVE_REVIEW_PROMPT = """请对以下直播场次进行复盘分析：

【基础数据】
- 产品品类：{category}
- 主推产品：{product_name}
- 直播时长：{duration}分钟
- 最高同时在线：{peak_viewers}人
- 平均在线：{avg_viewers}人
- 评论数：{comments}
- 点赞数：{likes}
- 下单人数：{orders}
- 成交金额：{gmv}元
- 退款率：{refund_rate}%

【话术/节奏描述】
{script_notes}

【商家自述问题】
{merchant_notes}

请返回JSON：
{{
  "overall_score": 75,
  "score_reason": "综合评分说明（2句话，口语）",
  "funnel": {{
    "enter_to_stay": "进场→停留转化分析（进场人数高/留存低的原因，口语30字内）",
    "stay_to_interact": "停留→互动分析",
    "interact_to_order": "互动→下单分析",
    "bottleneck": "最大漏斗问题在哪个环节（一句话）"
  }},
  "problems": [
    {{
      "type": "问题类型（话术/选品/节奏/信任/流量）",
      "title": "问题标题（10字内）",
      "desc": "具体问题描述（口语，40字内）",
      "severity": "高/中/低"
    }}
  ],
  "improvements": [
    {{
      "area": "改进方向（话术/选品/节奏/信任）",
      "action": "具体动作（口语，直接可执行，50字内）",
      "expected": "预期效果（量化，20字内）"
    }}
  ],
  "next_session_plan": {{
    "opening_30s": "下场开场前30秒话术建议（直接给一段口语稿，可念）",
    "product_order": "排品顺序建议（引流款→爆款→利润款，说明原因）",
    "timing": "直播时长和时间段建议",
    "key_focus": "下场最重要的1件事"
  }},
  "highlight": "这场做得最好的1点（肯定一下，不超过20字）"
}}"""


@dataclass
class LiveReviewRequest:
    category: str
    product_name: str
    duration: int = 120
    peak_viewers: int = 0
    avg_viewers: int = 0
    comments: int = 0
    likes: int = 0
    orders: int = 0
    gmv: float = 0.0
    refund_rate: float = 0.0
    script_notes: str = ""
    merchant_notes: str = ""


@dataclass
class LiveReviewResult:
    overall_score: int = 0
    score_reason: str = ""
    funnel: dict = field(default_factory=dict)
    problems: list = field(default_factory=list)
    improvements: list = field(default_factory=list)
    next_session_plan: dict = field(default_factory=dict)
    highlight: str = ""


class LiveReviewAgent:

    def analyze(self, req: LiveReviewRequest) -> LiveReviewResult:
        logger.info("LiveReviewAgent: product={} gmv={}", req.product_name, req.gmv)

        prompt = LIVE_REVIEW_PROMPT.format(
            category=req.category,
            product_name=req.product_name,
            duration=req.duration,
            peak_viewers=req.peak_viewers,
            avg_viewers=req.avg_viewers,
            comments=req.comments,
            likes=req.likes,
            orders=req.orders,
            gmv=req.gmv,
            refund_rate=req.refund_rate,
            script_notes=req.script_notes or "未填写",
            merchant_notes=req.merchant_notes or "未填写",
        )

        # Few-shot 注入
        samples = get_few_shot_samples(req.category, sample_type="live_module", count=2)
        few_shot_block = format_few_shot_block(samples, sample_type="live_module")
        system_prompt = LIVE_REVIEW_SYSTEM + ("\n\n" + few_shot_block if few_shot_block else "")

        try:
            raw = llm_service.chat_json(system_prompt, prompt)
        except Exception as exc:
            logger.error("LiveReviewAgent LLM失败: {}", exc)
            raw = self._fallback(req)

        return LiveReviewResult(
            overall_score=raw.get("overall_score", 60),
            score_reason=raw.get("score_reason", ""),
            funnel=raw.get("funnel", {}),
            problems=raw.get("problems", []),
            improvements=raw.get("improvements", []),
            next_session_plan=raw.get("next_session_plan", {}),
            highlight=raw.get("highlight", ""),
        )

    def _fallback(self, req: LiveReviewRequest) -> dict:
        cvr = round(req.orders / req.avg_viewers * 100, 1) if req.avg_viewers else 0
        return {
            "overall_score": 60,
            "score_reason": f"直播{req.duration}分钟，成交{req.orders}单，转化率{cvr}%，有提升空间。",
            "funnel": {
                "enter_to_stay": "数据待分析，建议记录开场10分钟的在线人数变化",
                "stay_to_interact": f"评论{req.comments}条，互动偏低，需增加提问互动",
                "interact_to_order": f"转化率{cvr}%，行业均值3-5%，需优化催单话术",
                "bottleneck": "互动→下单环节转化不足",
            },
            "problems": [
                {"type": "话术", "title": "催单话术弱", "desc": "没有制造足够的紧迫感，用户观望时间太长", "severity": "高"},
                {"type": "信任", "title": "产地展示不足", "desc": "缺少实拍产地/称重/采摘画面，信任感低", "severity": "中"},
            ],
            "improvements": [
                {"area": "话术", "action": "每15分钟用一次「库存只剩XX件」的紧迫感话术，配合截图展示", "expected": "转化率提升1-2%"},
                {"area": "信任", "action": "直播开场5分钟内实拍产地或称重，建立第一印象信任", "expected": "停留时长+20秒"},
            ],
            "next_session_plan": {
                "opening_30s": f"家人们好！我是{req.product_name}产地的老板，今天直接给大家看我家的货，不信你来看！",
                "product_order": "引流款先出（低价小规格），20分钟后出爆款，最后30分钟出利润款",
                "timing": f"建议保持{req.duration}分钟，晚8-10点时段流量最好",
                "key_focus": "开场就实拍产地，把信任建立在最前面",
            },
            "highlight": "坚持播完全场，这是很多新主播做不到的",
        }


live_review_agent = LiveReviewAgent()

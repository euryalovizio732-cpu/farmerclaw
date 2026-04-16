"""投放优化 Agent（DOU+ 建议）

基于：产品品类 + 视频基础数据 + 当前时令
输出：
  - 是否值得投 DOU+（判断逻辑）
  - 投放时间段建议（三农品类黄金时段）
  - 投放目标人群建议
  - 预算分配建议
  - 短期/长期投放策略
"""

from dataclasses import dataclass, field
from loguru import logger
from app.services.llm_service import llm_service
from app.services.knowledge_base import kb


AD_SYSTEM = """你是一位专注三农品类的抖音投放优化专家，熟悉DOU+投放规则和三农商家投放特性。

三农品类投放核心认知：
1. 三农商家预算有限，DOU+要「精投」不能「广投」
2. 投前必须判断视频是否「值得投」（完播率>40%、互动率>3%才有投放价值）
3. 三农品类黄金时段：
   - 水果/蔬菜：早6-8点（买菜时间）+ 晚8-10点（下班后零食）
   - 粮油：上午9-11点（家庭主妇购物时段）
   - 种子/化肥：上午8-11点（农民活跃时段）
4. 人群定向：30-55岁女性 + 有购买农产品记录 + 三四线城市为主
5. 投放目的：评论量>点赞量>粉丝量（电商转化看评论区）
6. 日常短视频投放预算：100-300元/条（新账号），成熟账号500-1000元

请基于数据给出可执行的投放建议，不说废话，要具体。

返回JSON格式。"""


AD_PROMPT = """请为以下三农视频给出DOU+投放建议：

【产品信息】
- 品类：{category}
- 产品：{product_name}
- 产地：{origin}
- 定价：{price}
- 当前节气：{solar_term}（{season}）

【视频基础数据】
- 视频类型：{video_type}（口播/产地探访/对比测评/知识科普）
- 自然播放量：{natural_views}
- 完播率：{completion_rate}%
- 点赞率：{like_rate}%（点赞/播放）
- 评论率：{comment_rate}%（评论/播放）
- 分享率：{share_rate}%（分享/播放）
- 视频时长：{duration}秒
- 发布时间：{publish_time}

【账号情况】
- 账号粉丝数：{followers}
- 账号主页历史视频平均播放：{avg_views}
- 近30天是否有违规：{has_violation}

【预算范围】
{budget}元

请返回JSON：
{{
  "should_boost": true,
  "should_boost_reason": "是否值得投放的判断（说清楚数据依据，口语，50字内）",
  "score": 75,
  "score_breakdown": {{
    "completion_score": "完播率评分（0-100，说明）",
    "engagement_score": "互动率评分（0-100，说明）",
    "content_score": "内容类型评分（0-100，说明）"
  }},
  "timing": {{
    "best_hours": ["19:00-21:00", "07:00-09:00"],
    "best_days": "工作日/周末/每天",
    "reason": "时间段选择原因（结合品类，30字）"
  }},
  "target_audience": {{
    "gender": "女性为主/男性为主/不限",
    "age": "30-45岁",
    "region": "三四线城市为主/不限",
    "interest": "精准兴趣标签建议（2-3个）",
    "reason": "人群选择说明（30字）"
  }},
  "budget_plan": {{
    "total": {budget},
    "phase1": "第一阶段（元/天×天数=总额，目标说明）",
    "phase2": "第二阶段（若效果好才执行）",
    "stop_signal": "什么数据出现就停投（具体阈值）"
  }},
  "objective": "投放目标（点赞/评论/主页访问/商品点击）及选择理由",
  "copy_suggestion": "投放配套的评论区置顶话术（直接可用，口语30字）",
  "risk": "投放风险提示（1条，30字内）"
}}"""


@dataclass
class AdRequest:
    category: str
    product_name: str
    origin: str = ""
    price: str = ""
    video_type: str = "口播"
    natural_views: int = 0
    completion_rate: float = 0.0
    like_rate: float = 0.0
    comment_rate: float = 0.0
    share_rate: float = 0.0
    duration: int = 30
    publish_time: str = ""
    followers: int = 0
    avg_views: int = 0
    has_violation: str = "无"
    budget: int = 300


@dataclass
class AdResult:
    should_boost: bool = False
    should_boost_reason: str = ""
    score: int = 0
    score_breakdown: dict = field(default_factory=dict)
    timing: dict = field(default_factory=dict)
    target_audience: dict = field(default_factory=dict)
    budget_plan: dict = field(default_factory=dict)
    objective: str = ""
    copy_suggestion: str = ""
    risk: str = ""


class AdAgent:

    def optimize(self, req: AdRequest) -> AdResult:
        logger.info("AdAgent: product={} views={} cr={}%", req.product_name, req.natural_views, req.completion_rate)

        season_info = kb.get_today_season()

        prompt = AD_PROMPT.format(
            category=req.category,
            product_name=req.product_name,
            origin=req.origin or "产地",
            price=req.price or "未填写",
            solar_term=season_info.get("solar_term", ""),
            season=season_info.get("season", ""),
            video_type=req.video_type,
            natural_views=req.natural_views,
            completion_rate=req.completion_rate,
            like_rate=req.like_rate,
            comment_rate=req.comment_rate,
            share_rate=req.share_rate,
            duration=req.duration,
            publish_time=req.publish_time or "未知",
            followers=req.followers,
            avg_views=req.avg_views,
            has_violation=req.has_violation,
            budget=req.budget,
        )

        try:
            raw = llm_service.chat_json(AD_SYSTEM, prompt)
        except Exception as exc:
            logger.error("AdAgent LLM失败: {}", exc)
            raw = self._fallback(req)

        return AdResult(
            should_boost=raw.get("should_boost", False),
            should_boost_reason=raw.get("should_boost_reason", ""),
            score=raw.get("score", 0),
            score_breakdown=raw.get("score_breakdown", {}),
            timing=raw.get("timing", {}),
            target_audience=raw.get("target_audience", {}),
            budget_plan=raw.get("budget_plan", {}),
            objective=raw.get("objective", ""),
            copy_suggestion=raw.get("copy_suggestion", ""),
            risk=raw.get("risk", ""),
        )

    def _fallback(self, req: AdRequest) -> dict:
        cr = req.completion_rate
        worth = cr >= 35 and req.natural_views >= 500
        category_hours = {
            "水果": ["07:00-09:00", "19:00-21:00"],
            "蔬菜": ["06:30-08:30", "17:00-19:00"],
            "粮油": ["09:00-11:00", "20:00-22:00"],
            "种子化肥": ["08:00-10:00", "14:00-16:00"],
        }
        hours = category_hours.get(req.category, ["19:00-21:00", "08:00-10:00"])

        return {
            "should_boost": worth,
            "should_boost_reason": (
                f"完播率{cr}%{'已达投放标准' if cr >= 35 else '偏低，建议先优化内容'}，"
                f"自然播放{req.natural_views}{'足够' if req.natural_views >= 500 else '不足'}，"
                f"{'建议投放' if worth else '暂不建议投，先提升内容质量'}"
            ),
            "score": min(100, int(cr * 1.5 + (30 if req.natural_views >= 500 else 0))),
            "score_breakdown": {
                "completion_score": f"完播率{cr}%，{'良好' if cr >= 35 else '偏低需改进'}",
                "engagement_score": f"互动率{'待评估' if not req.like_rate else f'{req.like_rate}%'}",
                "content_score": f"{req.video_type}类型，{'评论互动类最适合带货' if '口播' in req.video_type else '探访类信任感强'}",
            },
            "timing": {
                "best_hours": hours,
                "best_days": "每天",
                "reason": f"{req.category}品类用户活跃时段，此时下单意愿强",
            },
            "target_audience": {
                "gender": "女性为主",
                "age": "30-50岁",
                "region": "三四线城市为主",
                "interest": ["农产品", "生鲜水果", "家庭主妇"],
                "reason": "三农品类核心购买人群，价格敏感度较低",
            },
            "budget_plan": {
                "total": req.budget,
                "phase1": f"第一天投{min(req.budget, 100)}元，观察CTR和互动数据",
                "phase2": f"若CTR>3%继续投，追加{req.budget - min(req.budget, 100)}元",
                "stop_signal": "CTR低于1%或评论区出现大量负面即停投",
            },
            "objective": "评论量（带货场景评论区是成交关键，评论多=信任高）",
            "copy_suggestion": f"家人们！{req.product_name}今天还有货，评论区扣1我来回复你！",
            "risk": "投放期间确保客服在线，评论区有问题要快速回复",
        }


ad_agent = AdAgent()

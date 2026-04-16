"""今日内容包 Agent

将 TopicAgent + ListingAgent（脚本部分）串联为一个「今日内容包」交付物。
商家每天只需填一个表，3 分钟拿到：
  - 3 条选题（含封面建议+拍摄角度）
  - 3 条完整 30 秒口播稿（来自 ListingAgent，口语化，可直接念）
  - 模块化直播话术积木块（开场×3 / 互动×5 / 紧迫感×3 / 催单×3）
  - 今日推荐话题标签
  - 今日节气营销提示
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from loguru import logger

from app.services.topic_agent import topic_agent, TopicRequest, TopicResult
from app.services.listing_agent import listing_agent, ListingRequest, ListingResult
from app.services.knowledge_base import kb
from app.services.compliance_engine import compliance_engine
from app.services.script_agent import script_agent
from app.services.sample_library import SAMPLES


@dataclass
class ContentPackRequest:
    product_name: str
    category: str
    origin: str = ""
    specification: str = ""
    price: str = ""
    core_features: str = ""


@dataclass
class ContentPackResult:
    product_name: str
    category: str
    date: str = ""

    # 今日节气提示
    season_info: dict = field(default_factory=dict)
    today_tip: str = ""

    # 选题（来自 TopicAgent）
    topics: list[dict] = field(default_factory=list)

    # 口播稿（基于选题方向，生成 3 条对应口播）
    scripts: list[dict] = field(default_factory=list)   # [{topic_id, title, full_script}]

    # 直播话术积木块（来自知识库，已填充产品信息）
    live_modules: dict[str, list[dict]] = field(default_factory=dict)

    # 标签
    hashtags: list[str] = field(default_factory=list)

    # 合规状态
    compliance: dict[str, Any] = field(default_factory=dict)

    stages_completed: list[str] = field(default_factory=list)
    stages_failed: list[str] = field(default_factory=list)


class ContentPackAgent:
    """今日内容包 Agent"""

    def generate(self, request: ContentPackRequest) -> ContentPackResult:
        now = datetime.now()
        logger.info(
            "ContentPackAgent: product={} date={}",
            request.product_name, now.strftime("%Y-%m-%d")
        )

        result = ContentPackResult(
            product_name=request.product_name,
            category=request.category,
            date=now.strftime("%Y年%m月%d日"),
        )

        # ── Stage 1: 节气信息 ────────────────────────────
        result.season_info = kb.get_today_season()
        result.stages_completed.append("season")

        # ── Stage 2: 选题生成 ────────────────────────────
        try:
            topic_req = TopicRequest(
                product_name=request.product_name,
                category=request.category,
                origin=request.origin,
                core_features=request.core_features,
            )
            topic_result: TopicResult = topic_agent.generate(topic_req)
            result.topics = topic_result.topics
            result.today_tip = topic_result.today_tip
            result.hashtags = topic_result.hashtags
            result.stages_completed.append("topics")
            logger.info("Stage2 选题生成完成，{}条", len(result.topics))
        except Exception as exc:
            logger.error("Stage2 选题失败: {}", exc)
            result.stages_failed.append("topics")

        # ── Stage 3: 口播稿生成（按选题逐条生成，共3条） ──
        try:
            result.scripts, result.compliance, script_hashtags = self._build_scripts(result.topics, request)
            result.hashtags = self._normalize_hashtags(result.hashtags + script_hashtags, request)
            result.stages_completed.append("scripts")
            logger.info("Stage3 口播稿生成完成")
        except Exception as exc:
            logger.error("Stage3 口播稿失败: {}", exc)
            result.stages_failed.append("scripts")

        # ── Stage 4: 直播话术积木块（知识库，填充产品信息） ──
        try:
            result.live_modules = self._build_live_modules(request)
            result.stages_completed.append("live_modules")
        except Exception as exc:
            logger.error("Stage4 直播积木失败: {}", exc)
            result.stages_failed.append("live_modules")

        logger.info(
            "ContentPackAgent 完成: ok={} fail={}",
            result.stages_completed, result.stages_failed,
        )
        return result

    # ── 内部方法 ──────────────────────────────────────────

    def _extract_pain_hint(self, topics: list[dict]) -> str:
        """从选题中提取口播稿参考方向"""
        if not topics:
            return ""
        hints: list[str] = []
        for topic in topics[:2]:
            title = topic.get("title", "")
            conflict = topic.get("core_conflict", "")
            angle = topic.get("shooting_angle", "")
            if title:
                hints.append(f"标题：{title}")
            if conflict:
                hints.append(f"核心冲突：{conflict}")
            if angle:
                hints.append(f"拍摄角度：{angle}")
        return "；".join(hints)

    def _build_topic_angle(self, topic: dict) -> str:
        parts: list[str] = []
        if topic.get("title"):
            parts.append(f"标题：{topic['title']}")
        if topic.get("type"):
            parts.append(f"类型：{topic['type']}")
        if topic.get("core_conflict"):
            parts.append(f"核心冲突：{topic['core_conflict']}")
        if topic.get("shooting_angle"):
            parts.append(f"拍摄角度：{topic['shooting_angle']}")
        oral_keywords = topic.get("oral_keywords") or []
        if oral_keywords:
            parts.append("口播关键词：" + "、".join(oral_keywords[:4]))
        return "；".join(parts) or "围绕最强购买理由展开"

    def _serialize_compliance_issues(self, issues: list[Any]) -> list[dict[str, str]]:
        return [
            {
                "rule_id": issue.rule_id,
                "severity": issue.severity,
                "field": issue.field,
                "matched_text": issue.matched_text,
                "suggestion": issue.suggestion,
                "auto_fix": issue.auto_fix,
            }
            for issue in issues
        ]

    def _merge_compliance(self, issues: list[Any]) -> dict[str, Any]:
        critical_count = sum(1 for issue in issues if issue.severity == "critical")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        info_count = sum(1 for issue in issues if issue.severity == "info")
        return {
            "passed": critical_count == 0,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "issues": self._serialize_compliance_issues(issues),
        }

    def _normalize_hashtags(self, hashtags: list[str], request: "ContentPackRequest") -> list[str]:
        canonical_category = kb.resolve_best_category(request.product_name, request.category)
        candidates = list(hashtags)
        if request.product_name:
            candidates.append(f"#{request.product_name}")
        if canonical_category:
            candidates.append(f"#{canonical_category}")
        candidates.extend(["#三农", "#产地直发"])
        normalized: list[str] = []
        seen: set[str] = set()
        origin_text = (request.origin or "").replace(" ", "")
        for tag in candidates:
            cleaned = (tag or "").strip().replace(" ", "")
            if not cleaned:
                continue
            if not cleaned.startswith("#"):
                cleaned = f"#{cleaned.lstrip('#')}"
            if request.product_name and request.product_name in cleaned:
                if cleaned.count(request.product_name) > 1:
                    cleaned = f"#{request.product_name}"
                elif origin_text and origin_text in cleaned and cleaned != f"#{request.product_name}":
                    cleaned = f"#{request.product_name}"
            if cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)
        return normalized[:6]

    def _build_formula_context(self, request: "ContentPackRequest") -> dict[str, str]:
        canonical_category = kb.resolve_best_category(request.product_name, request.category)
        insights = kb.get_category_insights(canonical_category)
        season_info = kb.get_today_season()
        pricing = kb.get_market_pricing(canonical_category or request.product_name) or {}
        core_words = kb.get_category_core_words(canonical_category or request.category)
        product_traits = insights.get("product_traits", [])
        return {
            "节气": season_info.get("solar_term", "当季"),
            "产品": request.product_name,
            "品类": canonical_category or request.category or request.product_name,
            "产地": request.origin or insights.get("origin", "产地"),
            "时间": "今早六点",
            "天数": "三五",
            "高价": pricing.get("premium_brand", "商超价"),
            "低价": request.price or pricing.get("ecom_range", "产地直供价"),
            "海拔": "适宜产区",
            "温差": "昼夜温差大",
            "Brix": "按分级标准发货",
            "具体数量": "现货批次",
            "已售": "不少",
            "规格": request.specification or "当季规格",
            "备注": "优先发货",
            "新鲜特征": "果面状态和果粉完整",
            "批发价": pricing.get("wholesale_avg", "产地批发价"),
            "直播价": request.price or pricing.get("ecom_range", "产地直供价"),
            "差价": "中间环节加价",
            "价格": request.price or pricing.get("ecom_range", "产地直供价"),
            "单价": "更划算",
            "年限": "多年",
            "气候原因": "成熟窗口短",
            "比例": "少量异常直接处理",
            "关键特征": core_words[0] if core_words else "分级清楚",
            "场景记忆": "小时候院里摘下来就吃",
            "备注内容": "优先发货",
        }

    def _fill_formula_text(self, template: str, context: dict[str, str]) -> str:
        text = template
        for key, value in context.items():
            text = text.replace(f"{{{key}}}", value)
        return text

    def _build_scripts(
        self, topics: list[dict], request: "ContentPackRequest | None" = None
    ) -> tuple[list[dict], dict[str, Any], list[str]]:
        """
        3条口播稿，每条严格对应爆款三套公式结构：
          公式一（开场钩子）→ 公式二（买点中段）→ 公式三（结尾逼单）
        对标真实爆款案例：董宇辉大米买点思维 / 东方甄选脐橙溯源
        """
        script_topics = topics[:3] if topics else [{"topic_id": 1, "title": request.product_name if request else "默认口播", "type": "通用"}]
        all_issues: list[Any] = []
        hashtags: list[str] = []

        def _generate_one(idx_topic: tuple[int, dict]) -> dict:
            i, topic = idx_topic
            topic_title = topic.get("title", f"选题{i + 1}")
            topic_type = topic.get("type", "")
            
            # 使用新的 ScriptAgent 三段式流程
            script_context = {
                "origin": request.origin if request else "",
                "specification": request.specification if request else "",
                "price": request.price if request else "",
                "core_features": request.core_features if request else "",
            }
            
            refinement_result = script_agent.generate_with_review(
                product_name=request.product_name if request else topic_title,
                category=request.category if request else topic_type,
                topic_info=topic,
                context=script_context
            )
            
            full_script = refinement_result["full_script"]
            review_data = refinement_result["review"]
            
            # 合规检查（保留原有逻辑作为补充）
            issues = compliance_engine.check(full_script, "短视频口播")
            
            # 分段逻辑（简单按句点拆分或交给前端，这里保留原有字段结构）
            parts = [p.strip() for p in full_script.replace("！", "！\n").replace("。", "。\n").splitlines() if p.strip()]
            
            return {
                "_idx": i,
                "_issues": issues,
                "_hashtags": [], # 标签由 TopicAgent 统一出
                "topic_id": topic.get("topic_id", i + 1),
                "topic_title": topic_title,
                "topic_type": topic_type,
                "full_script": full_script,
                "review_score": review_data.get("score"),
                "review_suggestions": review_data.get("suggestions"),
                "hook_0_3s": parts[0] if len(parts) > 0 else "",
                "product_3_15s": " ".join(parts[1:3]) if len(parts) > 2 else "",
                "trust_15_25s": " ".join(parts[3:5]) if len(parts) > 4 else "",
                "cta_25_30s": " ".join(parts[5:]) if len(parts) > 5 else "",
                "formula_type": topic_type or ["知识反问", "季节稀缺", "产地溯源"][min(i, 2)],
            }

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(_generate_one, (i, t)): i for i, t in enumerate(script_topics)}
            raw_results = []
            for fut in as_completed(futures):
                try:
                    raw_results.append(fut.result())
                except Exception as exc:
                    logger.error("并行口播稿生成失败: {}", exc)

        raw_results.sort(key=lambda x: x["_idx"])
        scripts = []
        for r in raw_results:
            all_issues.extend(r.pop("_issues", []))
            hashtags.extend(r.pop("_hashtags", []))
            r.pop("_idx", None)
            scripts.append(r)

        return scripts, self._merge_compliance(all_issues), hashtags

    def _build_live_modules(self, request: ContentPackRequest) -> dict[str, list[dict]]:
        """填充知识库直播积木块中的产品变量"""
        raw_modules = kb.get_live_modules()
        product = request.product_name
        canonical_category = kb.resolve_best_category(request.product_name, request.category)
        insights = kb.get_category_insights(canonical_category)
        live_fill = kb.get_live_fill_values(canonical_category or request.category, request.product_name)
        origin = request.origin or insights.get("origin", "产地")
        price = request.price or "产地直供价"
        spec = request.specification or "一箱"

        season_info = kb.get_today_season()
        season_name = season_info.get("solar_term", "") if season_info else ""
        activity_name = f"{season_name}{product}尝鲜季" if season_name else f"{product}产地尝鲜季"
        core_advantage = request.core_features or "、".join((insights.get("quality_terms", []) + insights.get("product_traits", []))[:3]) or "产地直发，分级发货"
        review_line = "；".join(insights.get("ecommerce_facts", [])[:1]) or f"{product}按分级和时效发货"
        savings = live_fill.get("savings", "比商超同品质更划算")
        warranty = live_fill.get("warranty", "有问题直接走平台处理")

        def fill(script: str) -> str:
            text = (script
                .replace("{产品}", product)
                .replace("{产地}", origin)
                .replace("{价格}", price)
                .replace("{规格}", spec)
                .replace("{活动名称}", activity_name)
                .replace("{核心优势}", core_advantage)
                .replace("{外观特征}", live_fill.get("appearance", "状态在线"))
                .replace("{品质特征}", live_fill.get("quality", "分级发货"))
                .replace("{评价}", review_line)
                .replace("{节省}", savings)
                .replace("{节省金额}", "中间环节加价")
                .replace("{赠品}", "售后保障")
                .replace("{对比价}", "商超同品质价格")
                .replace("{库存数}", "这一批")
                .replace("{已售}", "不少")
                .replace("{时间}", "今晚")
                .replace("{品质描述}", live_fill.get("quality", "分级发货"))
                .replace("{比例}", warranty)
                .replace("{备注内容}", "优先发货")
            )
            return (text
                .replace("只有这一批件", "就是这一批现货")
                .replace("已经拍出去不少件了", "已经拍出去不少了")
                .replace("再过今晚这个季节就结束了", "这波时令窗口过去味道就不一样了")
                .replace("坏果超过有问题直接走平台处理全额退款", "坏果、破损拍照就走平台处理")
            )

        category_modules = sorted(
            SAMPLES.get(canonical_category, {}).get("live_module", []),
            key=lambda item: item.get("verified_hit", False),
            reverse=True,
        )
        type_map = {
            "开场暖场": "opening",
            "产品讲解": "product_intro",
            "产品展示": "product_intro",
            "场景种草": "product_intro",
            "互动留人": "interaction",
            "紧迫催单": "urgency",
            "收尾成交": "checkout",
        }
        tip_map = {
            "opening": "开播前30秒使用，先把人留住。",
            "product_intro": "讲产品和场景时穿插使用。",
            "interaction": "弹幕变少时穿插，拉互动。",
            "urgency": "临近成交时使用，放大时令窗口。",
            "checkout": "收口催单时使用，直接引导下单。",
        }

        filled: dict[str, list[dict]] = {module_type: [] for module_type in raw_modules}
        for index, module in enumerate(category_modules, 1):
            module_type = type_map.get(module.get("hook_type", ""), "product_intro")
            filled.setdefault(module_type, []).append({
                "id": f"{module_type}_{index}",
                "name": module.get("hook_type", f"{module_type}_{index}"),
                "script": fill(module.get("script", "")),
                "tips": tip_map.get(module_type, "按直播节奏灵活穿插。"),
            })

        for module_type, module_list in raw_modules.items():
            if filled.get(module_type):
                continue
            filled[module_type] = [
                {**m, "script": fill(m["script"])}
                for m in module_list
            ]
        return filled


content_pack_agent = ContentPackAgent()

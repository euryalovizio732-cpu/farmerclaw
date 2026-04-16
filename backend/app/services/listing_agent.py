"""三农 Listing 全自动生成 Agent

功能：产品信息 + 痛点报告 → 一键生成全套三农内容
输出：标题 + 卖点 + 详情页 + 主图脚本 + 短视频口播 + 直播话术

复用自 CrossClaw ListingAgent 架构（90%代码复用），
核心替换：Prompt体系 + 三农话术规则 + 生鲜合规校验。
"""

import json
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from app.services.llm_service import llm_service
from app.services.knowledge_base import kb
from app.services.compliance_engine import compliance_engine
from app.services.sample_library import get_few_shot_samples, format_few_shot_block


# ─── System Prompts ──────────────────────────────────

LISTING_SYSTEM_PROMPT = """你是一位深耕抖音三农电商的顶级内容运营专家，帮助数百家农业合作社和产地商家做到月销百万。
你的稿子对标的是：东方甄选脐橙溯源（2小时60万单）、董宇辉大米（情感买点4连单）、湘西村支书蜜桃（首场1600单）。

【核心原则：写"买点"不写"卖点"】
- 错误写法（卖点/商家视角）："产地优良、营养丰富、品质保证"——用户看完没感觉，不买
- 正确写法（买点/用户场景）："你买回家，早上给孩子榨杯汁，比果汁店便宜10倍，还是现摘的"——用户脑补画面，马上买
- 买点公式：用户的【生活场景】+【情感需求】+【省钱/省事/安心】

【爆款三段式结构（必须严格执行）】
第一段：开场钩子（0-3秒，决定完播率，必须直接开门见山）
  - 知识反问型："你知道为什么{节气}后的{产品}比前面贵一倍还抢着买吗？"
  - 价格冲击型："超市卖XX，今天产地直发XX，差价被谁赚走了我告诉你！"
  - 季节稀缺型："{节气}过了这{产品}就没了，一年就这几天，错过等明年！"
  - 产地溯源型："我现在就在{产地}地里，今天早上6点刚摘的，实地给你们拍！"
  ⚠️ 禁止以"大家好""欢迎来到"开头，这是废话，用户直接划走

第二段：卖点展示（3-25秒，用场景描述，不用产品参数）
  - 口感场景化：不说"糖度12度"→说"咬一口汁水往下流，不用纸巾擦都来不及"
  - 新鲜时间线：不说"当天发货"→说"今早6点摘的，今天下午就发，明天到你手上"
  - 产地知识："{产地}这里{地理优势}，老辈人传下来：{节气}后才摘，早一周口感差一半"
  - 零风险承诺："坏果直接拍给我，不用解释，二话不说直接退，连退款理由都不用填"

第三段：结尾逼单（25-30秒，行动指令必须具体到操作步骤）
  - 季节紧迫（三农最强武器）："{节气}结束后这个味道就没了，农村人都懂这个规律"
  - 行动指令：不说"需要的下单"→说"现在点右下角小黄车，选XX规格，拍完备注XX"
  - 季节时令紧迫：用"过了这个时间窗口"/"今年只剩这批"等真实季节原因，禁止编造具体库存件数

【口语化铁律】
- 每句不超过20字，短句，有节奏，说出来顺口
- 语气词：家人们、宝贝、真的、妥妥的
- 数字要具体，不能模糊，使用以下真实标准数据：
  * 脐橙糖度：特级≥11度，一级≥10度（国标GB/T 12947-2008）；高端如农夫山泉17.5°橙
  * 草莓糖度：优质品≥15度（行业通用标准）
  * 阳光玫瑰糖度：≥20度（巨峰15-18度）
  * 西瓜糖度：8-13度（正常范围）
  * 发货时效："今天采摘今天发，明天到货"（抖音2025年平均发货时长已缩短，48小时内发货为主流标准）
  * 不要说"很甜"→说"糖度11度以上，国标特级"；不要说"很新鲜"→说"今早6点采摘，下午发货"
- 情绪饱满，感叹号多用

【合规红线（违反就封号）】
- 禁止：治病/降血糖/消炎/根治（医疗宣传）
- 禁止：最好/第一/唯一/全国/极致（极限词）
- 禁止：无农残/100%有机/零农药（无认证不能说）
- 禁止：绝对好吃/保证新鲜（绝对性承诺）

【抖音平台规范】
- 标题≤30字，前15字必须有核心卖点
- 话题标签：#三农 #助农 #产地直发 #农人
- 口播30秒内，3段式结构

【真实数据铁律】
- 只能使用输入中提供的公开事实、价格带、品类知识和真实样本，不得编造亩数、销量、库存、资质、物流数字
- 如果没有具体事实，就写产地实拍、分级发货、冷链时效、售后流程，不能自由脑补

请严格按照JSON格式返回，字段完整，不要遗漏。"""


LISTING_USER_PROMPT_TEMPLATE = """请为以下农产品生成完整的电商内容：

  产品基础信息：
  - 产品名称：{product_name}
  - 品类：{category}
  - 产地：{origin}
  - 规格/重量：{specification}
  - 定价：{price}
  - 核心卖点：{core_features}
  - 平台：{platform}
 
  痛点参考（来自市场分析）：
  {pain_points_summary}

  本次口播必须围绕的选题方向：
  {content_angle}
 
  品类知识库关键词：
  {category_keywords}
 
  真实知识库事实：
  {fact_block}

高频种草词：
{core_words}

结构模板参考：
{listing_template}

真实价格参考：
{price_reference}

【⚠️ 生成前必须检查的7条铁律，缺一条都不合格】
铁律1-3秒钩子：口播稿第一句必须是反问/价格冲击/季节稀缺，禁止"大家好""看"开头
铁律2-价格锚定：必须使用用户提供的真实价格"{price}"，必须出现"超市XX→我们XX"的对比
铁律3-叠加承诺：必须包含至少3连赔（不正宗赔/不甜赔/坏果赔/不满意退），不能只说一个"坏果包赔"
铁律4-产地细节：必须提到具体种植工艺（如不催熟/不打蜡/自然成熟/冷链配送）
铁律5-口语化：每句不超过20字，用"家人们""真的""妥妥的"，禁止书面语
铁律6-互动指令：直播话术必须包含"扣1""点关注""点小黄车"等具体互动指令
铁律7-逼单紧迫：用真实时令/季节窗口制造紧迫感（如"过了这批时令就没这个口感了"），禁止编造任何具体库存件数（不得写"最后XX单/件"）

请生成以下JSON格式内容：
{{
  "title": "主标题（{title_limit}字以内，前15字必须有核心卖点/价格）",
  "subtitle": "副标题（15字内，含价格或促销信息）",
  "selling_points": [
    "卖点1：产地溯源（{origin}+具体种植细节，不催熟不打蜡）",
    "卖点2：品质指标（具体数字，如糖度XX度/果径XXmm）",
    "卖点3：配送承诺（顺丰/京东冷链+具体时效）",
    "卖点4：四重保障（不正宗赔+不甜赔+坏果赔+不满意退）",
    "卖点5：价格对比（超市XX→直播间{price}，具体省多少）"
  ],
  "detail_page": {{
    "product_intro": "产品介绍（200字，用买点写法：用户场景+情感需求+省钱省事）",
    "origin_story": "产地故事（150字，真人视角讲故事，突出'我们在这里种了X年'的真实感）",
    "quality_proof": "品质证明（100字，具体数据：糖度/果径/分级标准/检测报告）",
    "delivery_info": "配送说明（100字，泡沫箱+冰袋+网套三重防护+时效）",
    "after_sale": "售后保障（100字，四重承诺逐条写清）"
  }},
  "main_image_script": {{
    "scene_1": "主图1：产品切开特写，突出果肉汁水，大字标注到手价",
    "scene_2": "主图2：产地果园实拍，真人手持产品出镜",
    "scene_3": "主图3：规格实物对比（与手掌/硬币对比展示大小）",
    "scene_4": "主图4：四重保障图标",
    "scene_5": "主图5：好评截图拼图+产地/发货实拍"
  }},
  "video_script": {{
    "hook_0_3s": "（铁律1：反问/价格冲击/季节稀缺开场，口语，例：家人们！你知道超市的{product_name}卖多少吗？）",
    "product_show_3_15s": "（铁律4+5：产地细节+口语化描述，例：今早6点刚摘的，不催熟不打蜡，咬一口汁水往下流！）",
    "trust_15_25s": "（铁律3：叠加承诺，例：不正宗包赔！不甜包赔！坏果包赔！不满意直接退！拍个照就赔！）",
    "cta_25_30s": "（铁律7：具体操作+紧迫感，例：点右下角小黄车，选{specification}，手慢就没了家人们！）",
    "full_script": "完整30秒口播稿（以上四段连起来，全口语，可直接对着镜头念）"
  }},
  "live_script": {{
    "opening": "（铁律6：开场+互动，例：家人们来了啊！想要{product_name}的扣个1！新来的点个关注！）",
    "product_intro": "（铁律2+4：产地+品质+价格锚定，例：超市同品质XX元，我们直播间{price}包邮到家！）",
    "urgency": "（铁律7：用真实时令窗口，例：过了这个季节就没这个口感了！现在摘的才是最甜的！）",
    "trust_and_after_sale": "（铁律3：四重承诺完整版，打消一切顾虑）",
    "checkout": "（铁律6+7：操作步骤+最后冲刺，例：点小黄车第一个链接！拍完扣'拍了'优先发货！）"
  }},
  "seo_keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "hashtags": ["#话题标签1", "#话题标签2", "#话题标签3"]
}}"""


@dataclass
class ListingRequest:
    product_name: str
    category: str
    origin: str = "产地"
    specification: str = ""
    price: str = ""
    core_features: str = ""
    platform: str = "douyin"
    pain_points_summary: str = ""   # 来自痛点报告的摘要（可选）
    content_angle: str = ""


@dataclass
class ListingResult:
    title: str
    subtitle: str
    selling_points: list[str]
    detail_page: dict[str, str]
    main_image_script: dict[str, str]
    video_script: dict[str, str]
    live_script: dict[str, str]
    seo_keywords: list[str]
    hashtags: list[str]
    compliance: dict[str, Any] = field(default_factory=dict)
    platform: str = "douyin"
    raw_output: str = ""


class AgriculturalListingAgent:
    """三农 Listing 全自动生成 Agent

    工作流：
    1. 知识库注入（品类关键词 + 模板）
    2. LLM 生成全套内容
    3. 合规引擎校验 + 自动修复
    4. 返回结构化 Listing 结果
    """

    def __init__(self):
        self._llm = llm_service
        self._kb = kb
        self._compliance = compliance_engine

    def generate(self, request: ListingRequest) -> ListingResult:
        logger.info(
            "ListingAgent: 开始生成 product={} platform={}",
            request.product_name, request.platform
        )

        # 1. 知识库注入
        canonical_category = self._kb.resolve_best_category(request.product_name, request.category)
        category_kw = self._kb.get_category_keywords(canonical_category or request.category)
        category_insights = self._kb.get_category_insights(canonical_category)
        fact_block = self._kb.build_fact_block(canonical_category or request.product_name, request.platform)
        core_words = self._kb.get_category_core_words(canonical_category or request.category)
        listing_template = self._kb.get_listing_template(canonical_category or request.category)
        market_pricing = self._kb.get_market_pricing(canonical_category or request.product_name)
        title_limit = self._kb.get_platform_title_limit(request.platform)
        platform_name = self._format_platform(request.platform)

        # 把知识库关键词格式化为字符串
        kw_str = ""
        for kw_type, kws in list(category_kw.items())[:3]:
            kw_str += f"{kw_type}：{', '.join(kws[:5])}\n"

        template_str = ""
        if listing_template:
            title_formula = listing_template.get("title_formula", "")
            selling_points = listing_template.get("selling_points", [])
            template_parts = []
            if title_formula:
                template_parts.append(f"标题公式：{title_formula}")
            if selling_points:
                template_parts.append("卖点骨架：" + "；".join(selling_points[:3]))
            template_str = "\n".join(template_parts)

        price_reference = (
            f"批发均价{market_pricing['wholesale_avg']}；电商常见价格带{market_pricing['ecom_range']}；"
            f"价格趋势{market_pricing['wholesale_trend']}；来源{market_pricing['source']}"
            if market_pricing
            else "暂无明确公开价格带，优先按产地直发、商超对比和分级发货表达"
        )

        # 1b. Few-shot 注入：获取真实样本，注入 System Prompt
        sample_key = canonical_category or request.category
        samples = get_few_shot_samples(sample_key, sample_type="script", count=3)
        if len(samples) < 3 and request.product_name != sample_key:
            extra = get_few_shot_samples(request.product_name, sample_type="script", count=3 - len(samples))
            samples.extend(extra)
        few_shot_block = format_few_shot_block(samples, sample_type="script")
        if few_shot_block:
            system_prompt = LISTING_SYSTEM_PROMPT + "\n\n" + few_shot_block
            logger.info("ListingAgent: 注入{}条真实样本（品类:{}）", len(samples), sample_key)
        else:
            system_prompt = LISTING_SYSTEM_PROMPT
            logger.debug("ListingAgent: 样本库未就绪（{}），使用纯指令模式生成", sample_key)

        # 2. 构建 Prompt
        user_prompt = LISTING_USER_PROMPT_TEMPLATE.format(
            product_name=request.product_name,
            category=canonical_category or request.category,
            origin=request.origin or category_insights.get("origin", "产地"),
            specification=request.specification or "多规格可选",
            price=request.price or "产地直供价",
            core_features=request.core_features or "、".join(core_words[:4]) or f"新鲜{request.category}，产地直发",
            platform=platform_name,
            title_limit=title_limit,
            pain_points_summary=request.pain_points_summary or "用户关注：新鲜度、物流速度、售后保障",
            content_angle=request.content_angle or "无固定选题，优先围绕最强购买理由展开",
            category_keywords=kw_str,
            fact_block=fact_block or "- 暂无额外事实，优先强调产地实拍、分级发货、售后承诺",
            core_words="、".join(core_words[:8]) or "产地直发、分级发货、坏果包赔",
            listing_template=template_str or "标题先写产地和规格，卖点按产地-品质-配送-售后-价格展开",
            price_reference=price_reference,
        )

        # 3. 调用 LLM
        try:
            raw = self._llm.chat_json(system_prompt, user_prompt)
        except Exception as exc:
            logger.error("ListingAgent LLM 调用失败: {}", exc)
            raw = self._fallback_listing(request, title_limit)

        # 4. 提取字段（容错处理）
        title = raw.get("title", f"新鲜{request.product_name}|产地直发|坏果包赔")
        subtitle = raw.get("subtitle", "产地直供，新鲜到家")
        selling_points = raw.get("selling_points", [])
        detail_page = raw.get("detail_page", {})
        main_image_script = raw.get("main_image_script", {})
        video_script = raw.get("video_script", {})
        live_script = raw.get("live_script", {})
        seo_keywords = raw.get("seo_keywords", [])
        hashtags = raw.get("hashtags", [])

        # 5. 合规检测
        compliance_result = self._compliance.check_listing(
            title=title,
            selling_points=selling_points,
            detail_page=detail_page.get("product_intro", ""),
            video_script=video_script.get("full_script", ""),
            live_script=live_script.get("product_intro", ""),
            platform=request.platform,
        )

        # 6. 自动修复标题（如有违规）
        if not compliance_result["passed"]:
            title = self._compliance.auto_fix_text(title)
            selling_points = [self._compliance.auto_fix_text(sp) for sp in selling_points]
            logger.warning(
                "ListingAgent: 发现{}个critical问题，已自动修复",
                compliance_result["critical_count"]
            )

        result = ListingResult(
            title=title,
            subtitle=subtitle,
            selling_points=selling_points,
            detail_page=detail_page,
            main_image_script=main_image_script,
            video_script=video_script,
            live_script=live_script,
            seo_keywords=seo_keywords,
            hashtags=hashtags,
            compliance=compliance_result,
            platform=request.platform,
            raw_output=json.dumps(raw, ensure_ascii=False),
        )

        logger.info(
            "ListingAgent: 生成完成，合规={} critical问题={}",
            compliance_result["passed"], compliance_result["critical_count"]
        )
        return result

    def _format_platform(self, platform: str) -> str:
        return {
            "douyin": "抖音小店",
            "pinduoduo": "拼多多",
            "huinong": "惠农网",
            "taobao": "淘宝",
            "jd": "京东",
        }.get(platform, platform)

    def _fallback_listing(self, req: ListingRequest, title_limit: int) -> dict:
        """LLM 不可用时的规则兜底（融入7条铁律 + 真实市场数据）"""
        canonical_category = self._kb.resolve_best_category(req.product_name, req.category)
        insights = self._kb.get_category_insights(canonical_category)
        core_words = self._kb.get_category_core_words(canonical_category or req.category)
        name = req.product_name
        origin = req.origin or insights.get("origin", "产地")
        price = req.price or ""
        spec = req.specification or ""
        features = req.core_features or "、".join(core_words[:3])
        title = f"{origin}{name}现摘现发|{spec or '产地直发'}|坏果包赔"[:title_limit]

        # 从知识库获取真实定价数据做价格锚定
        market = self._kb.get_market_pricing(name)
        if market and price:
            price_anchor_line = (
                f"公开价格带在{market['ecom_range']}，我们{origin}产地直发，"
                f"{spec}{price}到手，少了中间商加价！"
            )
        elif price:
            price_anchor_line = f"今天{spec}{price}，产地直发不赚差价，交个朋友！"
        else:
            price_anchor_line = f"产地直发价，比超市便宜一大截，{spec}到手价看小黄车！"

        # 节气信息
        season = self._kb.get_today_season()
        season_name = season.get("solar_term", "") if season else ""
        season_angle = season.get("angle", "") if season else ""

        # 口播稿 - 严格7条铁律
        hook = (
            f"家人们！你知道超市一个{name}多少钱吗？"
            if not season_name
            else f"家人们！{season_name}之后的{name}才是最好吃的，老农民都知道这个规律！"
        )

        product_show = (
            f"你看这个{name}，"
        )
        if features:
            product_show += f"{features}！"
        else:
            product_show += f"{('、'.join(insights.get('product_traits', [])[:2]) or '分级清楚、状态在线')}，{origin}出来的味道更稳！"
        product_show += f"今天早上刚从地里摘的，下午就给你发出去！"

        trust = (
            f"担心品质？咱们四个承诺：不正宗包赔！不甜包赔！坏果包赔！不满意直接退！"
            f"拍个照发过来，二话不说直接赔，连理由都不用填！"
        )

        cta = f"现在点右下角小黄车，选{spec or name}，拍完就发货！手慢就没了家人们！"

        full_script = f"{hook}\n{product_show}\n{trust}\n{cta}"

        # 直播话术 - 模块化 + 互动指令 + 逼单紧迫
        live_opening = (
            f"家人们来了啊！新来的宝贝先点个关注，"
            f"今天我在{origin}给你们直播发福利！"
            f"想要{name}的先扣个1，让我看看有多少人！"
        )

        live_product = (
            f"来看这个{name}，{origin}自家果园种的！"
        )
        if features:
            live_product += f"{features}！"
        if price:
            live_product += f"超市你去看看，同品质什么价？我们直播间{price}，{spec}给你包邮到家！"
        else:
            live_product += f"产地直发，中间商一分钱不赚！"
        live_product += f"今天采摘今天发，顺丰冷链，坏了算我的！"

        live_urgency = (
            f"家人们！今天的货就这些了，卖完真没了！"
            f"已经下了200多单了，库存就剩最后一点！"
            f"犹豫的时候别人已经拍完了！3、2、1上链接！"
        )

        live_trust = (
            f"老粉都知道，我家{name}从来不让你们失望！"
            f"四个承诺：不正宗赔！不甜赔！坏果赔！不满意直接退！"
            f"收到货有任何问题，拍照发给客服，秒退！"
            f"我们做的是口碑，不是一锤子买卖！"
        )

        live_checkout = (
            f"想要的现在就拍！点右下角小黄车，第一个链接！"
            f"{name}{spec}{price + '，' if price else ''}拍完备注你要的规格！"
            f"拍完了的扣个'拍了'，我给你优先发货！"
        )

        return {
            "title": title,
            "subtitle": f"产地直发，坏果包赔{'，' + price if price else ''}",
            "selling_points": [
                f"🌱 {origin}直采，{(insights.get('production_facts', ['今天摘今天发'])[0])}",
                f"✅ {features or name + '品质优良'}，按分级标准发货，不混装不乱发",
                f"🚚 顺丰/京东冷链48小时送达，全程保鲜",
                f"🔒 四重保障：不正宗赔、不甜赔、坏果赔、不满意直接退",
                f"💰 {price_anchor_line}",
            ],
            "detail_page": {
                "product_intro": (
                    f"我们的{name}来自{origin}，自家果园种植。"
                    f"{'核心优势：' + features + '。' if features else ''}"
                    f"每一颗都经过人工精选分级，确保到手品质。"
                    f"不催熟、不打蜡，自然成熟的味道，吃过就知道区别。"
                ),
                "origin_story": (
                    f"{origin}是这类产品的核心产区之一。"
                    f"{(insights.get('production_facts', ['这里做的是产地直发'])[0])}"
                    f"我们内容里不玩虚的，拍到什么就发什么。"
                ),
                "quality_proof": (
                    f"按分级标准和发货批次挑货。"
                    f"{(insights.get('ecommerce_facts', ['发货前人工复检，不达标不发出'])[0])}"
                ),
                "delivery_info": (
                    f"采用顺丰/京东冷链配送，48小时内送达。"
                    f"泡沫箱+冰袋+网套三重防护，确保运输不破损。"
                ),
                "after_sale": (
                    f"四重保障：不正宗赔、不甜赔、坏果赔、不满意退！"
                    f"{('；'.join(insights.get('reply_tips', [])[:2]) or '收到有问题拍照走平台处理，我们第一时间响应。')}"
                ),
            },
            "main_image_script": {
                "scene_1": f"主图1：{name}切开特写，突出果肉色泽和汁水，大字标注'{price or '产地价'}到手'",
                "scene_2": f"主图2：{origin}果园实拍，主播手持{name}，真人出镜增加信任",
                "scene_3": f"主图3：{spec}实物与手掌/硬币对比，展示真实大小",
                "scene_4": f"主图4：四重保障图标（不正宗赔/不甜赔/坏果赔/不满意退）",
                "scene_5": f"主图5：好评截图拼图 + 产地发货实拍",
            },
            "video_script": {
                "hook_0_3s": hook,
                "product_show_3_15s": product_show,
                "trust_15_25s": trust,
                "cta_25_30s": cta,
                "full_script": full_script,
            },
            "live_script": {
                "opening": live_opening,
                "product_intro": live_product,
                "urgency": live_urgency,
                "trust_and_after_sale": live_trust,
                "checkout": live_checkout,
            },
            "seo_keywords": [
                f"{name}产地直发", f"新鲜{name}", f"{origin}{name}",
                f"{name}坏果包赔", f"{name}{spec}" if spec else f"{name}包邮",
            ],
            "hashtags": [f"#{name}", f"#{canonical_category or name}", "#产地直发", "#坏果包赔", "#三农"],
        }


listing_agent = AgriculturalListingAgent()
